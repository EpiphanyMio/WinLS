# WinLS 0.1.0 beta.1

Windows 定位模拟器预发布版。包含 iOS 17+ 实体设备、Android 实体设备及 HarmonyOS 7+ 的开发者模拟定位支持。

- `WinLS-0.1.0-beta.1-Windows-Setup.exe`：Windows 10/11 64 位安装程序。

此版本修复了 Windows 安装后的启动与地图显示问题，并将 iPhone 定位所需的 Wintun 组件打包进安装程序。

iPhone 需安装 Apple Mobile Device Support；Android 需安装 ADB Platform-Tools；原生 HarmonyOS 7+ 需安装 hdc。这些设备连接组件不包含在 Windows 安装程序中。完整步骤见仓库 README。

此版为 beta。Windows 图形界面、地图显示及实体 iPhone 定位已在本地验证；Android、HarmonyOS 设备组合尚未完成端到端验证。Windows 安装程序未签名。
