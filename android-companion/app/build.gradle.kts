plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.windowslocationsimulator.mock"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.windowslocationsimulator.mock"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-beta.1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
