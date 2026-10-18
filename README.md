# Global Xiaomi Watch 5 — German language resource comparison

I own the **Chinese Xiaomi Watch 5 running HyperOS 3**. My phone is set to German, but the watch interface remains in English. I am investigating whether German translations can be adapted while retaining the original China firmware and the features I use, including **ECG and blood pressure**.

I am looking for help from someone who owns the **global Xiaomi Watch 5 running Wear OS**, expected codename **blenny / O61W**. Its system resources can help us compare the two versions. Compatibility between Wear OS and HyperOS still needs to be checked.

## Download the English guide and export tool

**[Download Watch5-Global-Export-English-1.1.zip](https://raw.githubusercontent.com/Sumski24/sumski-ai-android/watch5-global-export/Watch5-Global-Export-English-1.1.zip)**

The ZIP contains the instructions and export tool. It does **not** contain a Xiaomi firmware image.

- [Complete English instructions](README-English.txt)
- [Message explaining why I am asking](Message-to-global-Watch5-owner.txt)
- [Inspect the Python export tool](export_watch5.py)
- [Windows launcher](START-WINDOWS.cmd)

## How to help

1. Download and extract the ZIP.
2. Follow **README-English.txt** to prepare Python and Google's Android Platform Tools.
3. Connect the **global watch** to the computer using wireless ADB.
4. Run **START-WINDOWS.cmd** on Windows, or `python3 export_watch5.py` on macOS/Linux.
5. Return the **generated export ZIP** to the person requesting it. It appears inside the `exports` folder. Please also state whether the watch interface was set to German during the export.

The tool copies readable **system APKs, installed language splits, Android framework resources, Xiaomi framework JARs and available MCU firmware/resource archives**. Source paths, sizes, local SHA-256 hashes and failed/skipped copies are recorded in the export.

If you already have the **original full global OTA ZIP or its official download URL**, that would also be useful.

## Scope and current testing

- No root or bootloader unlock is required.
- The tool does not install apps, flash firmware, reboot the watch or change its language/region.
- It does not collect personal app data, account tokens or health databases.
- It creates files on the computer and reads files on the watch.
- This is a **resource comparison export**, not a complete partition dump or a restorable ROM backup.
- Only accessible files and currently installed split APKs can be copied. Missing MCU archives do not prove the watch has no separate MCU resources.
- The exporter has passed local checks using a **simulated ADB device**, including global-device acceptance, China/phone rejection, language split copying, transfer-failure handling and ZIP/hash verification. It has **not yet been tested by the author on a physical global Watch 5**.

The tool has a 1 GiB individual-file limit and a 4 GiB default total copied-data limit. Skipped files are listed in its report.

## Download integrity

SHA-256 of the downloadable ZIP:

`c3df18177206f993ac5e7cb6cce5d728c64de3bd94f93127eaf31d15318fc188`

## References

- [Google: Debug Wear OS over Wi-Fi](https://developer.android.com/training/wearables/get-started/debug-wifi)
- [Google: Android Debug Bridge](https://developer.android.com/tools/adb)
- [Google: Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
- [Watch model/codename registry](https://github.com/KHwang9883/MobileModels/blob/master/brands/xiaomi-wear.md)

