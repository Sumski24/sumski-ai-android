#!/usr/bin/env python3
"""Copy readable global Watch 5 system resources to the computer over ADB.

No third-party Python modules. No writes, installs, setters or root calls on
the watch. This is a comparison export, not a complete partition image.
"""
import argparse
import datetime
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

VERSION = "1.1"
MIB = 1024 * 1024
PROPERTIES = (
    "ro.product.manufacturer", "ro.product.brand", "ro.product.model",
    "ro.product.device", "ro.product.name", "ro.product.vendor.device",
    "ro.product.system.device", "ro.build.fingerprint",
    "ro.build.version.incremental", "ro.build.version.release",
    "ro.build.version.sdk", "ro.build.version.security_patch",
    "ro.product.cpu.abilist", "persist.sys.locale",
    "ro.miwear.build.region", "persist.miwear.region",
)
MCU_KNOWN = (
    "/system/miwear/ota/mcu_res_ota.zip",
    "/vendor/firmware/vela_ota.zip",
    "/system/miwear/ota/mcu_ota.zip",
)
MCU_ROOTS = (
    "/system/miwear/ota", "/vendor/firmware", "/vendor/etc/firmware",
    "/product/miwear/ota", "/system_ext/miwear/ota",
)
CORE_PACKAGES = {"android", "com.android.settings", "com.android.systemui",
                 "com.android.launcher3"}


class ExportError(Exception):
    pass


class Adb:
    def __init__(self, executable, serial=None):
        self.executable = str(executable)
        self.serial = serial

    def run(self, *args, timeout=30):
        command = [self.executable]
        if self.serial:
            command += ["-s", self.serial]
        try:
            return subprocess.run(command + list(args), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise ExportError("ADB timed out: " + str(args[0])) from exc
        except OSError as exc:
            raise ExportError("Cannot run ADB: " + str(exc)) from exc

    def shell(self, command, timeout=30):
        return self.run("shell", command, timeout=timeout)


def find_adb(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if p.is_file():
            return p
        raise ExportError("ADB executable not found: " + str(p))
    base = Path(__file__).resolve().parent
    name = "adb.exe" if sys.platform == "win32" else "adb"
    for p in (base / "platform-tools" / name, base / name):
        if p.is_file():
            return p
    path = shutil.which("adb")
    if path:
        return Path(path)
    raise ExportError("ADB not found. Extract Google's platform-tools folder "
                      "next to this script, or put adb on PATH.")


def choose_device(adb, requested):
    result = adb.run("devices")
    if result.returncode:
        raise ExportError(result.stderr.strip() or "adb devices failed")
    online = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "device":
            online.append(fields[0])
    if requested:
        if requested not in online:
            raise ExportError("The requested watch is not connected/authorized. "
                              "Check adb devices and the watch confirmation.")
        return requested
    if len(online) != 1:
        raise ExportError("Connect exactly one watch, or pass --serial with its "
                          "identifier from adb devices. Online devices: "
                          + str(len(online)))
    return online[0]


def properties(adb):
    result = {}
    for name in PROPERTIES:
        r = adb.shell("getprop " + shlex.quote(name))
        if r.returncode:
            raise ExportError("Cannot read device property " + name)
        result[name] = r.stdout.strip()
    return result


def package_names(text):
    return sorted({line[len("package:"):].strip() for line in text.splitlines()
                   if line.startswith("package:")
                   and re.fullmatch(r"[A-Za-z0-9._]+", line[len("package:"):].strip())})


def confirm_global_watch(info, inventory, features):
    maker = (info.get("ro.product.manufacturer", "") + " " +
             info.get("ro.product.brand", "")).lower()
    identifiers = " ".join(info.get(k, "") for k in (
        "ro.product.device", "ro.product.vendor.device",
        "ro.product.system.device", "ro.build.fingerprint"))
    if "xiaomi" not in maker:
        raise ExportError("This is not an identified Xiaomi device. No export made.")
    if ("CNXM" in info.get("ro.build.version.incremental", "").upper()
            or any(info.get(k, "").lower() == "cn" for k in
                   ("ro.miwear.build.region", "persist.miwear.region"))):
        raise ExportError("China firmware/region detected. This export requires "
                          "the GLOBAL Wear OS Watch 5. No export made.")
    if not re.search(r"(?<![A-Za-z0-9])blenny(?![A-Za-z0-9])", identifiers, re.I):
        raise ExportError("Expected global Watch 5 codename blenny was not found. "
                          "Send the displayed model/build for review; do not "
                          "change the script's device check.")
    if "android.hardware.type.watch" not in features:
        raise ExportError("The Android watch feature was not confirmed.")
    if not any(p.startswith(("com.google.android.wearable", "com.google.android.apps.wearable",
                             "com.google.android.clockwork", "com.google.android.apps.clockwork"))
               for p in inventory):
        raise ExportError("Google Wear OS system packages were not confirmed.")


def wanted_package(name):
    return (name in CORE_PACKAGES
            or name.startswith(("com.xiaomi.", "com.miui.", "com.mi.",
                                "com.google.android.wearable", "com.google.android.apps.wearable",
                                "com.google.android.clockwork", "com.google.android.apps.clockwork"))
            or ("overlay" in name.lower() and name.startswith(("com.android.", "com.google.", "com.xiaomi."))))


class Collector:
    def __init__(self, adb, folder, max_total):
        self.adb = adb
        self.folder = folder
        self.max_total = max_total
        self.total = 0
        self.entries = []
        self.seen = set()
        self.notes = []

    def note(self, message):
        self.notes.append(message)
        print(message, flush=True)

    def pull(self, remote, relative, kind):
        if remote in self.seen:
            return
        self.seen.add(remote)
        entry = {"source": remote, "file": relative, "kind": kind}
        self.entries.append(entry)
        target = None
        try:
            check = self.adb.shell("[ -f " + shlex.quote(remote) + " ] && [ -r "
                                   + shlex.quote(remote) + " ] && stat -L -c %s "
                                   + shlex.quote(remote))
            if check.returncode or not check.stdout.strip().isdigit():
                entry["status"] = "missing_or_unreadable"
                if check.stderr.strip():
                    entry["error"] = check.stderr.strip()[-2000:]
                return
            size = int(check.stdout.strip())
            entry["source_bytes"] = size
            if size <= 0 or size > 1024 * MIB or self.total + size > self.max_total:
                entry["status"] = "size_limit"
                self.note("SKIPPED (size limit): " + remote)
                return
            if shutil.disk_usage(self.folder).free < size + 256 * MIB:
                raise ExportError("Not enough free space on the computer.")
            target = self.folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            self.note("Copying: " + remote + " (" + str(size) + " bytes)")
            result = self.adb.run("pull", remote, str(target), timeout=600)
            if result.returncode or not target.is_file() or target.stat().st_size != size:
                entry["status"] = "copy_failed"
                entry["error"] = (result.stderr or result.stdout)[-2000:]
                if target.is_file():
                    target.unlink()
                return
            digest = hashlib.sha256()
            with target.open("rb") as handle:
                for block in iter(lambda: handle.read(MIB), b""):
                    digest.update(block)
            entry.update(status="copied", bytes=size, sha256=digest.hexdigest())
            self.total += size
        except ExportError as exc:
            entry.update(status="failed", error=str(exc))
            if target is not None and target.is_file():
                target.unlink()
            self.note("FAILED: " + str(exc))

    def firmware(self):
        for remote in MCU_KNOWN:
            self.pull(remote, "firmware" + remote, "mcu_firmware")
        for root in MCU_ROOTS:
            try:
                command = ("if [ -d " + shlex.quote(root) + " ]; then find "
                           + shlex.quote(root) + " -maxdepth 4 -type f "
                           + "\\( -name '*.zip' -o -name '*.bin' -o -name '*.img' "
                           + "\\) 2>/dev/null; fi")
                result = self.adb.shell(command, timeout=45)
                for remote in result.stdout.splitlines()[:200]:
                    if not remote.startswith(root + "/") or ".." in remote.split("/"):
                        continue
                    if ("/miwear/ota/" in remote
                            or re.search(r"vela|mcu|i18n|locale|language", remote, re.I)):
                        self.pull(remote, "firmware" + remote, "mcu_firmware")
            except ExportError as exc:
                self.note("Optional firmware scan: " + str(exc))

    def apks(self, inventory):
        selected = sorted((p for p in inventory if wanted_package(p)),
                          key=lambda p: (p not in CORE_PACKAGES, not p.startswith("com.xiaomi."), p))
        for package in selected:
            try:
                result = self.adb.shell("pm path " + shlex.quote(package))
                paths = [line[len("package:"):].strip() for line in result.stdout.splitlines()
                         if line.startswith("package:")]
                if result.returncode or not paths:
                    self.note("Package paths unavailable: " + package)
                    continue
                for index, remote in enumerate(paths, 1):
                    if not remote.startswith("/") or not remote.endswith(".apk"):
                        continue
                    name = re.sub(r"[^A-Za-z0-9._-]", "_", remote.rsplit("/", 1)[-1])
                    self.pull(remote, "apks/" + package + "/" + str(index) + "-" + name,
                              "system_apk")
            except ExportError as exc:
                self.note("Package scan: " + str(exc))
        self.pull("/system/framework/framework-res.apk", "framework/framework-res.apk",
                  "android_resources")

    def frameworks(self):
        for root in ("/system/framework", "/system_ext/framework", "/product/framework"):
            try:
                result = self.adb.shell("ls -1 " + shlex.quote(root))
                for name in result.stdout.splitlines():
                    if (re.fullmatch(r"[A-Za-z0-9._-]+[.]jar", name)
                            and re.search(r"wear|miui|xiaomi|cpc", name, re.I)):
                        remote = root + "/" + name
                        self.pull(remote, "framework" + remote, "framework_jar")
            except ExportError as exc:
                self.note("Optional framework scan: " + str(exc))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", help="Optional full path to adb/adb.exe")
    parser.add_argument("--serial", help="Watch identifier shown by adb devices")
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent / "exports")
    parser.add_argument("--max-total-mib", type=int, default=4096)
    args = parser.parse_args(argv)
    if args.max_total_mib < 1:
        raise ExportError("--max-total-mib must be positive")
    adb = Adb(find_adb(args.adb))
    adb.serial = choose_device(adb, args.serial)
    info = properties(adb)
    print("Model: " + info.get("ro.product.model", ""))
    print("Device: " + info.get("ro.product.device", ""))
    print("Build: " + info.get("ro.build.version.incremental", ""))
    packages_result = adb.shell("pm list packages -s")
    features_result = adb.shell("pm list features")
    inventory = package_names(packages_result.stdout)
    if packages_result.returncode or not inventory or features_result.returncode:
        raise ExportError("System package/feature inventory could not be read. "
                          "Please send the console output for review.")
    confirm_global_watch(info, inventory, features_result.stdout)
    root = args.output_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = Path(tempfile.mkdtemp(prefix="Watch5-Global-Export-" + stamp + "-", dir=root))
    (folder / "Device.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    (folder / "System-packages.txt").write_text(packages_result.stdout, encoding="utf-8")
    (folder / "Features.txt").write_text(features_result.stdout, encoding="utf-8")
    collector = Collector(adb, folder, args.max_total_mib * MIB)
    collector.firmware()
    collector.apks(inventory)
    collector.frameworks()
    copied = [e for e in collector.entries if e.get("status") == "copied"]
    apk_count = sum(e["kind"] in ("system_apk", "android_resources") for e in copied)
    mcu_count = sum(e["kind"] == "mcu_firmware" for e in copied)
    report = ("GLOBAL XIAOMI WATCH 5 COMPARISON EXPORT " + VERSION + "\n"
              + "This is NOT a complete ROM/partition backup.\n"
              + "Device files were read over ADB; no watch files were modified.\n"
              + "Copied files: " + str(len(copied)) + "\n"
              + "APK/resource files: " + str(apk_count) + "\n"
              + "MCU firmware files: " + str(mcu_count) + "\n"
              + "Copied bytes: " + str(collector.total) + "\n"
              + "All package paths returned by pm path were considered, including splits.\n"
              + "Missing/unreadable/oversized files are recorded in Manifest.json.\n"
              + "Local SHA-256 hashes identify the copied files.\n")
    if mcu_count == 0:
        report += "No readable MCU package was found at the searched locations. This does not prove it is absent.\n"
    if apk_count == 0:
        report += "PARTIAL: No APK resources were copied. Send the report for troubleshooting.\n"
    (folder / "Report.txt").write_text(report, encoding="utf-8")
    (folder / "Notes.txt").write_text("\n".join(collector.notes) + "\n", encoding="utf-8")
    (folder / "Manifest.json").write_text(json.dumps(collector.entries, indent=2) + "\n",
                                          encoding="utf-8")
    archive = folder.with_suffix(".zip")
    print("Creating ZIP on the computer...", flush=True)
    if shutil.disk_usage(root).free < collector.total + 256 * MIB:
        raise ExportError("Not enough space for the ZIP. The exported files remain at " + str(folder))
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as output:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                output.write(path, str(Path(folder.name) / path.relative_to(folder)))
    print(report)
    print("SEND THIS FILE: " + str(archive), flush=True)
    return 0 if apk_count else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ExportError, OSError, zipfile.BadZipFile) as error:
        print("STOP: " + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopped by user. Any completed PC copies remain in exports.", file=sys.stderr)
        sys.exit(130)
