import java.util.Base64

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

tasks.matching { it.name == "assembleRelease" }.configureEach {
    doFirst {
        val definitions = project.findProperty("dart-defines")?.toString().orEmpty()
            .split(",")
            .filter { it.isNotBlank() }
            .map { String(Base64.getDecoder().decode(it)) }
        val apiUrl = definitions.firstOrNull { it.startsWith("HAAZIR_API_URL=") }
            ?.substringAfter("=")
        check(apiUrl?.startsWith("https://") == true) {
            "Release requires --dart-define=HAAZIR_API_URL=https://.../api/v1"
        }
    }
}

android {
    namespace = "com.nadhalabs.haazir"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.nadhalabs.haazir"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // Local verification only. Configure an upload keystore in CI before store distribution.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
