# WinLS 0.1.0

Windows 定位模拟器正式版。支持 iOS 17+、Android 与 HarmonyOS 7+ 实体设备的开发者模拟定位。

- 跑道模板改为约 400 米，并限制所选长直边短于 200 米。
- 已绘制的路径点可在地图上拖动调整，坐标文本和路线草稿会同步更新。
- 自动查找常见 HarmonyOS SDK 路径中的 `hdc`；缺失时提供华为官方工具安装入口。
- 支持单点定位、路线回放、地图选点与搜索、配置导入导出。

下载 `WinLS-0.1.0-Windows-Setup.exe` 安装。iPhone 需 Apple Mobile Device Support；Android 需 ADB Platform-Tools 和配套 APK；HarmonyOS 7+ 需华为 SDK 中的 `hdc`。设备连接步骤见 README。

首次正式发布。HarmonyOS 实体设备尚未完成端到端验证。安装程序未签名。

