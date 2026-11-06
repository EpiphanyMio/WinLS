# 定位模拟器 · Windows

这是独立的 Windows 桌面项目。功能以 Mac 版 `LocationSimulator` 1.1.0 为参考：iPhone 和 Android 实体设备的单点定位、路径循环模拟、地图选点和搜索、学校附近运动场地、1000 米跑道模板、配速与动态速度、平滑路线偏移、JSON 配置导入导出、搜索历史和路线草稿记忆。配置 JSON 与 Mac 版 `schemaVersion: 1` 兼容。地图数据来自 OpenStreetMap；搜索使用 Nominatim，选中学校后使用 Overpass 查找运动场地，结果覆盖范围可能与 Apple 地图不同。

## Windows 上运行

1. 安装 Windows 10/11、Python 3.12（64 位）、Apple Devices 或 Apple 官网的 iTunes（包含 Apple Mobile Device Support/USB 驱动）。将 iPhone 用 USB 连接、解锁并点按“信任此电脑”。在 iPhone 设置中开启“开发者模式”并按提示重启。需要 iOS 17 或更新版本。
2. 在 PowerShell 中运行：

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pymobiledevice3 usbmux list --simple --usb
   .\.venv\Scripts\python.exe -m winloc.app
   ```

3. 点击“刷新”选择设备。单点定位可直接输入坐标、在地图上选点或搜索地点；路线可在地图上逐点绘制，也可切换到“坐标文本”后应用。点击“开始模拟”后每约 0.5 秒发送一次坐标。“停止”保留当前坐标，“清除定位”清除开发者模拟定位。退出程序会尝试清除定位并结束设备会话。

Windows 无法运行 Apple 的 Xcode iOS Simulator，因此 Mac 版的 iOS 模拟器设备选项在 Windows 上没有对应设备；本程序的 iOS 定位目标是连接的实体 iPhone。

若设备列表为空，先确认驱动已安装、USB 连接和信任状态。`pymobiledevice3 usbmux list --simple --usb` 是连接诊断的第一步。服务连接失败时，检查开发者模式以及 iOS 与 pymobiledevice3 的兼容性。某些设备准备步骤可能需要更新 Apple 驱动或完成配对。地图、地点搜索需要网络；手动坐标和设备通信可离线使用。

## 打包

在 Windows PowerShell 执行 `powershell -ExecutionPolicy Bypass -File scripts\build.ps1`。输出目录为 `dist\WindowsLocationSimulator`；这是目录式程序，需连同目录中的依赖一起分发。当前构建会附带控制台窗口，以便设备桥接进程通过标准输入输出通信并显示诊断信息。Android 功能还需要单独安装 ADB Platform-Tools 和下述手机配套 App。尚未在真实 Windows 主机和实体手机上完成端到端测试，分发前应在目标系统验证安装、发现设备、设置和清除定位、路线运行。程序未签名。

## Android 实体设备

1. 在 Windows 安装 [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)，把 `adb.exe` 所在目录加入 PATH。手机开启开发者选项和 USB 调试，连接后确认 `adb devices -l` 显示状态 `device`。
2. 使用 Android Studio 打开 `android-companion`，安装 Android SDK 35 和 JDK 17+，构建 `app` 的 debug APK。也可在项目目录运行 `gradlew.bat :app:assembleDebug`。生成的 APK 位于 `app\build\outputs\apk\debug\app-debug.apk`。安装：`adb install -r app\build\outputs\apk\debug\app-debug.apk`。
3. 在手机上**打开一次**“定位模拟器配套应用”，然后在开发者选项的“选择模拟位置信息应用”中选择它。返回 Windows 程序刷新设备，选中 Android 设备后即可使用单点定位、路线模拟、停止和清除。配套 App 支持 Android 8.0/API 26 及更新版本，不需要 root。

Windows 端通过 ADB 向配套 App 的受限广播接收器发送坐标。接收器只接受持有 Android `DUMP` 权限的发送者（ADB shell），并返回明确的成功或错误结果；App 使用 `LocationManager` 的 GPS 和网络测试位置提供者。USB 断开、App 未安装或未被选为模拟定位应用时，Windows 程序会显示失败。部分 App 会识别模拟位置或使用其他定位来源，厂商系统行为也可能不同。Android 模拟器的 `adb emu geo fix` 仅适用于模拟器，本项目的 Android 功能面向实体设备。

## 验证

运行 `python -m unittest discover -s tests -v` 验证配置兼容、轨迹、跑道、动态速度及 ADB 命令。实体设备验证需在 Windows/iPhone/Android 环境进行。项目仅用于开发与测试。
