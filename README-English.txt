GLOBAL XIAOMI WATCH 5: FIRMWARE AND LANGUAGE RESOURCE EXPORT
Version 1.1 | 18 October 2026

WHY I AM ASKING

Hi! I own the Chinese Xiaomi Watch 5 running HyperOS 3. My phone is set to German, but the watch interface remains in English.

I would like to investigate whether a German interface can be added while keeping the original China firmware and the features I use, including ECG and blood pressure.

Could you help by providing a read-only export from your GLOBAL Xiaomi Watch 5 running Wear OS? We need its system APKs, installed language splits, framework files and any accessible MCU firmware/resource packages to compare the German translations with the Chinese version. Compatibility between Wear OS and HyperOS still needs to be checked.

The attached English guide includes an export tool. It does not require root, modify the watch firmware or collect personal app data or health databases.

If you already have the full global OTA ZIP or its official download link, that would also be very useful.

Thank you for helping!


TECHNICAL PURPOSE

We need files from a genuine GLOBAL Xiaomi Watch 5 running Wear OS to compare
its German system resources with the China HyperOS Watch 5. The export can
help identify usable translations and firmware components. It does not prove
that these can be installed on the China watch.

The supplied PC script copies readable system APKs, their split APKs (including
language splits when installed), Android framework resources, Xiaomi framework
JARs and any readable MCU firmware/resource archives found at the searched
locations. This includes mcu_res_ota.zip if present and readable.

It does not root the watch, unlock its bootloader, install an app, change the
region/language, reboot it, read health databases or modify watch files. The
exported files and the final ZIP are created on the COMPUTER.

IMPORTANT LIMITATION

This is a system-resource export, NOT a complete raw ROM/partition dump or a
restorable backup. A normal production ADB shell may not read protected block
devices or updater-private files. Missing MCU files are reported honestly.
If you already have the original full GLOBAL OTA ZIP or its direct download
URL, please provide that as well. It is the preferred source for a full image.
An incremental OTA may require its matching base firmware.

1. CHECK THE WATCH

Use the GLOBAL Xiaomi Watch 5, expected codename "blenny", with Wear OS.
The China HyperOS model is "grass" and is not the donor needed here.
The script checks the device, system packages and firmware region before
copying anything. If it stops because the model is unrecognized, send the
displayed model/device/build for review instead of removing the check.

2. PREPARE THE COMPUTER

You need Windows, macOS or Linux, Python 3.9 or newer, and Google's current
Android SDK Platform Tools. No additional Python packages are required.

Python: https://www.python.org/downloads/
Platform Tools: https://developer.android.com/tools/releases/platform-tools

Extract this guide's ZIP into a folder. Also extract Google's Platform Tools
ZIP there so that the layout is:

  Watch5-Global-Export-English/
    README-English.txt
    export_watch5.py
    START-WINDOWS.cmd
    platform-tools/
      adb.exe       (Windows; keep the supplied DLLs next to it)
      adb           (macOS/Linux)

Use the Platform Tools package for YOUR computer. Alternatively, adb may
already be on PATH. Leave enough free space for both the copied files and the
ZIP: around 8 GB accommodates the default 4 GiB copied-data limit plus the ZIP.
Individual files above 1 GiB and files exceeding the total limit are recorded
as skipped; these limits mean the export may be incomplete.

3. ENABLE WIRELESS DEBUGGING ON THE WATCH

Connect the watch and computer to the same Wi-Fi network.
On the WATCH, open Settings > System > About > Versions and tap the build
number repeatedly until Developer options are enabled. Menu wording can vary.
Open Developer options and enable ADB debugging and Wireless debugging, where
those switches are available. Choose "Pair new device" or "Pair using pairing
code". Keep the pairing screen open.

This ADB pairing is with the computer. Keep the existing Mi Fitness pairing.

Official instructions:
https://developer.android.com/training/wearables/get-started/debug-wifi

4. PAIR AND CONNECT ADB

Open a terminal in the platform-tools folder.
In Windows Command Prompt run:

  adb.exe pair WATCH_IP:PAIRING_PORT

On macOS/Linux use ./adb instead of adb.exe.
In Windows PowerShell use .\adb.exe instead of adb.exe.

Replace WATCH_IP and PAIRING_PORT with the values on the watch. Enter the
pairing code when prompted; do not include the pairing code in files you send.

Go back to the main Wireless debugging screen. Use its connection address:

  adb.exe connect WATCH_IP:CONNECTION_PORT
  adb.exe devices

PAIRING_PORT and CONNECTION_PORT are usually different. Copy each one from
the relevant screen. Accept any authorization prompt on the watch.
The watch must appear with status "device", not "offline" or "unauthorized".
A normal charging cable/cradle is not assumed to provide USB data access.

5. RUN THE EXPORT

Windows: return to the guide folder and double-click START-WINDOWS.cmd.

macOS/Linux: open a terminal in the guide folder and run:

  python3 export_watch5.py

The terminal displays the model, device and build, then the files being copied.
Keep the watch connected and allow the process to finish. Large MCU resource
archives can take several minutes over Wi-Fi.

If multiple ADB devices are connected, use the watch identifier from
"adb devices" explicitly. Run from the guide folder:

  Windows: START-WINDOWS.cmd --serial WATCH_IP:CONNECTION_PORT
  macOS/Linux: python3 export_watch5.py --serial WATCH_IP:CONNECTION_PORT

If you need a different ADB location, add --adb followed by its full path.

6. SEND THE ACTUAL EXPORT ZIP

At the end, look for:

  SEND THIS FILE: .../exports/Watch5-Global-Export-<date>-<time>-<id>.zip

Send THAT generated ZIP, not the small instruction ZIP you started with.
Please also tell us whether the watch interface was set to German during
the export. Only currently installed split APKs can be copied.
It contains the actual APK/JAR/firmware files plus:

  Device.json            Model, build, Android version, locale and region
  System-packages.txt    System-package inventory
  Features.txt           Android feature inventory
  Manifest.json          Source paths, sizes, copy results and SHA-256 hashes
  Report.txt             Summary, limits and missing-component information
  Notes.txt              Copy progress and any errors

Please keep the original APK, JAR and firmware files unchanged. If the export
is too large to attach, upload the generated ZIP to a file host you choose and
provide its download link. Review the archive before sharing it: it contains
build information and system-package names, but the script does not collect
accounts, authentication tokens, personal app data or health databases.

An export with APKs but no MCU package is still useful for Android translation
analysis. It is not evidence that the watch has no separate MCU resources.

TROUBLESHOOTING

- ADB not found: check the folder layout or use --adb with the exact path.
- No device/offline/unauthorized: reconnect using the CURRENT connection port
  and check the confirmation on the watch.
- China firmware/unknown codename: stop and send the displayed build details.
- Permission denied: keep the report; do not change permissions or use root.
- Cannot read package inventory: send the console output for review.
- Space/size limit reached: the report records the skipped files. Do not call
  the result a complete ROM dump.
- The script has been checked locally with a simulated ADB device; it has not
  been run on a physical global Watch 5 by its author. Device-specific access
  restrictions can require a follow-up adjustment.

After finishing, you can turn wireless/ADB debugging back off on the watch.

SOURCES

ADB file copying and device selection:
https://developer.android.com/tools/adb
Wear OS debugging:
https://developer.android.com/training/wearables/get-started/debugging
https://developer.android.com/training/wearables/get-started/debug-wifi
Device/codename reference:
https://github.com/KHwang9883/MobileModels/blob/master/brands/xiaomi-wear.md
Android A/B OTA architecture:
https://source.android.com/docs/core/ota/ab
