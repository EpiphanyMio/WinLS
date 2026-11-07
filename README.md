# 定位模拟器 · Windows

这是独立的 Windows 桌面项目。功能以 Mac 版 `LocationSimulator` 1.1.0 为参考：iPhone、Android 和 HarmonyOS 7+ 实体设备的单点定位、路径循环模拟、地图选点和搜索、学校附近运动场地、400 米跑道模板、配速与动态速度、平滑路线偏移、JSON 配置导入导出、搜索历史和路线草稿记忆。配置 JSON 与 Mac 版 `schemaVersion: 1` 兼容。地图界面所需的 Leaflet 和 WebChannel 脚本随程序提供；底图瓦片仍需连接 OpenStreetMap，搜索使用 Nominatim，选中学校后使用 Overpass 查找运动场地，结果覆盖范围可能与 Apple 地图不同。

## Windows 上运行

1. 安装 Windows 10/11 和 Python 3.12（64 位）。若要连接 iPhone，还需安装 Apple Devices 或 Apple 官网的 iTunes（包含 Apple Mobile Device Support/USB 驱动）。将 iPhone 用 USB 连接、解锁并点按“信任此电脑”；开启“开发者模式”并按提示重启。iPhone 需要 iOS 17 或更新版本。Android 和 HarmonyOS 的连接准备见下文。
2. 在 PowerShell 中运行：

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m winloc.app
   ```

3. 点击“刷新”选择设备。单点定位可直接输入坐标、在地图上选点或搜索地点；路线可在地图上逐点绘制，已绘制点可拖动调整，也可切换到“坐标文本”后应用。iPhone 和 Android 的路线约每 0.5 秒发送一次坐标；HarmonyOS 路线由设备端按 GPX 回放，间隔至少 1 秒。“停止”保留当前坐标，“清除定位”恢复设备默认定位。退出程序会尝试清除定位并结束设备会话。

Windows 无法运行 Apple 的 Xcode iOS Simulator，因此 Mac 版的 iOS 模拟器设备选项在 Windows 上没有对应设备；本程序的 iOS 定位目标是连接的实体 iPhone。

若设备列表为空，先确认驱动已安装、USB 连接和信任状态。`pymobiledevice3 usbmux list --simple --usb` 是连接诊断的第一步。服务连接失败时，检查开发者模式以及 iOS 与 pymobiledevice3 的兼容性。某些设备准备步骤可能需要更新 Apple 驱动或完成配对。地图、地点搜索需要网络；手动坐标和设备通信可离线使用。

### iOS 驱动检测

点击目标设备旁的“检查 iOS 驱动”，可查看 Apple Mobile Device Service 是否安装并运行、Apple USB 驱动是否可检测、以及是否安装爱思助手。刷新设备时，如果 Windows 检测到连接的 Apple USB 设备但没有找到 iPhone，也会自动显示诊断。爱思助手只作为诊断线索；即使它已安装，程序仍以 Apple 服务和驱动的实际检测结果判断是否就绪。

若提示缺少组件，优先安装或更新 [Apple Devices（微软商店）](https://apps.microsoft.com/detail/9np83lwlpz9k)，或从 [Apple 官网](https://www.apple.com/itunes/)安装 iTunes；若已经安装爱思助手，也可使用其驱动修复功能。安装后重启电脑，重新连接并解锁 iPhone，选择“信任此电脑”。若服务已安装但未运行，在 `services.msc` 中启动或重启 Apple Mobile Device Service。仍不能识别时参考 [Apple 官方连接排查](https://support.apple.com/en-us/108643)。驱动检测是只读检查；在不同版本的 Apple 驱动和 Windows 上，未检测到并不必然代表组件不存在。

## 打包

在 Windows PowerShell 执行 `powershell -ExecutionPolicy Bypass -File scripts\build.ps1`。输出目录为 `dist\WindowsLocationSimulator`；这是目录式程序，需连同目录中的依赖一起分发。当前构建会附带控制台窗口，以便设备桥接进程通过标准输入输出通信并显示诊断信息。Android 功能还需要单独安装 ADB Platform-Tools 和下述手机配套 App。尚未在真实 Windows 主机和实体手机上完成端到端测试，分发前应在目标系统验证安装、发现设备、设置和清除定位、路线运行。程序未签名。

## iOS 实体设备
本产品对iOS设备完美适配，利用iOS的开发者套件，可以实现更底层的定位修改。实测小程序校园跑可完美兼容。

## Android 实体设备

1. 在 Windows 安装 [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)，把 `adb.exe` 所在目录加入 PATH。手机开启开发者选项和 USB 调试，连接后确认 `adb devices -l` 显示状态 `device`。
2. 使用 Android Studio 打开 `android-companion`，安装 Android SDK 35 和 JDK 17+，构建 `app` 的 debug APK。也可在项目目录运行 `gradlew.bat :app:assembleDebug`。生成的 APK 位于 `app\build\outputs\apk\debug\app-debug.apk`。安装：`adb install -r app\build\outputs\apk\debug\app-debug.apk`。
3. 在手机上**打开一次**“定位模拟器配套应用”，然后在开发者选项的“选择模拟位置信息应用”中选择它。返回 Windows 程序刷新设备，选中 Android 设备后即可使用单点定位、路线模拟、停止和清除。配套 App 支持 Android 8.0/API 26 及更新版本，不需要 root。

Windows 端通过 ADB 向配套 App 的受限广播接收器发送坐标。接收器只接受持有 Android `DUMP` 权限的发送者（ADB shell），并返回明确的成功或错误结果；App 使用 `LocationManager` 的 GPS 和网络测试位置提供者。USB 断开、App 未安装或未被选为模拟定位应用时，Windows 程序会显示失败。部分 App 会识别模拟位置或使用其他定位来源，厂商系统行为也可能不同。Android 模拟器的 `adb emu geo fix` 仅适用于模拟器，本项目的 Android 功能面向实体设备。

## HarmonyOS 实体设备

原生 HarmonyOS 7.0.0 及以上设备可使用华为官方 [testhelper 位置模拟命令](https://developer.huawei.com/consumer/cn/doc/HarmonyOS-Guides/testhelper-guidelines/)。在 Windows 安装 DevEco Studio 或华为 [Command Line Tools](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-commandline-get)，手机开启开发者选项和 USB 调试并授权电脑。程序会自动检查 PATH 和常见 SDK 安装目录；若找不到 `hdc`，点击刷新后会询问是否打开华为官方安装说明。安装/解压后再次刷新，程序会自动发现常见 SDK 路径并在本次运行中配置 `hdc`，不必手动修改系统 PATH。也可将 SDK 的 `toolchains` 目录（包含 `hdc.exe`）加入 PATH。确认设备已授权后，选择“HarmonyOS 设备”。单点和路线都通过 hdc 向设备发送 GPX，再由 `testhelper` 回放；清除定位会恢复真实位置。

testhelper 每个 GPX 最多支持 1000 个位置点，更新间隔必须是 1～3600 秒的整数。程序会按路线时长自动选取间隔，并在设备端回放期间保留停止功能；因此 HarmonyOS 路线的时间和位置精度可能低于 iPhone/Android 约 0.5 秒一次的更新。设备端若返回“不支持位置模拟”，程序会显示具体错误。程序退出时会尝试关闭通过本程序启用的模拟定位。连接方式和 hdc 安装见 [华为官方 hdc 文档](https://developer.huawei.com/consumer/en/doc/harmonyos-guides/hdc/)。

仍可安装 APK 的较早 HarmonyOS 版本可尝试上面的 Android/ADB 配套 App 路径；原生 HarmonyOS 设备不要安装该 APK。此项目尚未在实体 HarmonyOS 设备上完成端到端验证。

## 验证

运行 `python -m unittest discover -s tests -v` 验证配置兼容、轨迹、跑道、动态速度、ADB/HDC 命令及 iOS 驱动诊断。实体设备验证需在 Windows/iPhone/Android/HarmonyOS 环境进行。项目仅用于开发与测试。

