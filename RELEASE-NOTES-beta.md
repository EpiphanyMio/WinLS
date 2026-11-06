# WinLS 0.1.0 beta.1

Windows 定位模拟器预发布版。包含 iOS 17+ 实体设备、Android 实体设备及 HarmonyOS 7+ 的开发者模拟定位支持。

- `WinLS-0.1.0-beta.1-Windows-Setup.exe`：Windows 10/11 64 位安装程序。
- `WinLS-0.1.0-beta.1-Android.apk`：Android 模拟定位配套应用。安装后须在开发者选项中选择为模拟位置信息应用。兼容 APK 的较早 HarmonyOS 版本可尝试使用此方式。

iPhone 需安装 Apple Mobile Device Support；Android 需安装 ADB Platform-Tools；原生 HarmonyOS 7+ 需安装 hdc。这些设备连接组件不包含在 Windows 安装程序中。完整步骤见仓库 README。

此版为 beta，尚未在真实 Windows/实体 iPhone、Android、HarmonyOS 设备组合上完成端到端验证。Android APK 为 debug 签名，仅用于开发测试；Windows 安装程序未签名。
