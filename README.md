# Sumski AI 1.0 – Android Wrapper

Native Android WebView wrapper for the Jotform app:

- App ID: `262474589430364`
- Public URL: `https://www.jotform.com/app/262474589430364`
- Package: `com.sumski.ai`
- Version: `1.0.0`
- Minimum Android: 8.0 (API 26)
- Target/Compile SDK: Android 15 / API 35

## Included
- Fullscreen WebView
- JavaScript and DOM storage
- File upload / attachments
- Microphone and camera web permissions
- Back navigation inside the app
- External non-Jotform links open in the normal browser
- Dark splash screen and Sumski AI icon
- GitHub Actions workflow that builds `app-debug.apk`

## Build in Android Studio
1. Open this folder as an Android Studio project.
2. Let Gradle sync complete.
3. Choose **Build > Build APK(s)**.
4. The APK is created under:
   `app/build/outputs/apk/debug/app-debug.apk`

## Build with GitHub Actions
1. Upload the complete project to a GitHub repository.
2. Open **Actions > Build Sumski AI APK**.
3. Run the workflow.
4. Download the artifact **Sumski-AI-1.0-APK**.

Note: This wrapper loads the Jotform-hosted app. The Jotform app must therefore remain accessible at its public app URL.
