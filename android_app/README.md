# 错题快速转换助手 - 安卓端 (Android App)

本项目是 Windows 版错题快速转换助手的 **Android 原生移植版**。基于 **Kotlin + Android 无障碍服务 (AccessibilityService)** 开发，实现了在安卓手机端任何软件（微信、QQ、钉钉、小红书、备忘录等）中，键入 `135qqq` 即时自动擦除并展开为预设错题文案的功能。

---

## ✨ 核心特性

1. **⚡ 无障碍即时自动展开（核心）**：
   - 无论使用何种输入法（微信输入法、搜狗、百度、讯飞或手机系统自带输入法）；
   - 在任何输入框打出 `135` 紧接着键入 `qqq`（如 `135qqq` 或 `1 3 12qqq`），系统瞬间擦除输入字符并就地展开为：  
     `本次作业的错题题号为：1，3，5`。
2. **📱 系统级划选文本就地替换 (Process Text)**：
   - 在任何文本框长按选中数字（如 `135`），弹出的系统浮动菜单（复制/剪切旁）会出现 **「转为错题格式」**，点击一键替换。
3. **🎨 现代 Material 3 界面**：
   - 支持自定义触发词（可自由修改为 `..`、`fff` 等）；
   - 支持自由编辑文案模板（如 `{nums}` 动态占位符）与一键预设；
   - 支持自由切换分隔符（中文逗号 `，`、顿号 `、`、空格等）；
   - 内置实时测试预览卡片与一键复制功能。

---

## 📂 项目结构

```text
android_app/
│
├── app/
│   ├── build.gradle.kts           # App 模块构建依赖配置
│   ├── src/
│   │   ├── main/
│   │   │   ├── AndroidManifest.xml # 核心清单元件，声明无障碍服务与划选菜单
│   │   │   ├── java/com/transcriber/homework/
│   │   │   │   ├── MainActivity.kt        # 主设置界面（配置模板、触发词、权限状态检测）
│   │   │   │   ├── ProcessTextActivity.kt # 划选文本快捷替换 Activity
│   │   │   │   ├── core/
│   │   │   │   │   ├── TextProcessor.kt   # 智能数字切分与模板格式化引擎（算法完全同 Python 版）
│   │   │   │   │   └── ConfigManager.kt   # SharedPreferences 本地持久化配置管理
│   │   │   │   └── service/
│   │   │   │       └── TextExpanderService.kt # 核心无障碍文本监听与自动替换服务
│   │   │   └── res/                       # 界面布局、色彩与无障碍服务配置文件
│   │   └── test/                          # 核心算法单元测试用例
│
├── autoxjs/                               # 免编译运行方案
│   └── 错题转换助手.js                    # AutoX.js 脚本版，支持直接在手机上一键导出 APK
│
├── build.gradle.kts                       # 根工程构建脚本
├── settings.gradle.kts                    # 工程设置
└── README.md                              # 本说明文档
```

---

## 🛠️ 构建与安装指南

### 方式 1：使用 Android Studio 编译与安装（推荐）

1. 下载并安装 [Android Studio](https://developer.android.google.cn/studio/)；
2. 打开 Android Studio，点击 **Open**，选择本项目中的 `android_app` 文件夹；
3. 等待 Gradle 同步完成；
4. 连接安卓手机（开启 USB 调试）或启动模拟器，点击顶部绿色的 **Run ('app')** 按钮；
5. 或在菜单栏选择 **Build -> Build Bundle(s) / APK(s) -> Build APK(s)**，即可在 `app/build/outputs/apk/debug/` 下获得安装包 `app-debug.apk`。

---

### 方式 2：使用 AutoX.js 在手机上一键生成 APK（免装 Android Studio）

如果你电脑上没有配置 Android Studio 开发环境，又想立即在手机上拥有独立 App：

1. 手机上安装现成的 **[AutoX.js](https://github.com/kkevsekk1/AutoX)**；
2. 将 `autoxjs/错题转换助手.js` 导入到 AutoX.js 中；
3. 在 AutoX.js 中点击该脚本右侧的 **「打包」** 按钮，几秒钟即可在手机本地生成一个安装包并安装！

---

## 📖 手机端使用说明

1. 安装并打开 **错题快速转换助手** App；
2. 顶部状态栏会提示：`⚠️ 无障碍服务未开启`，点击旁边的 **「去开启」**；
3. 系统将自动跳转至系统的【无障碍 / 辅助功能】设置页，在已安装的服务中找到 **「错题快速转换助手 - 自动展开服务」** 并开启；
4. 切换到微信、QQ、备忘录等任何聊天或输入窗口：
   - 连续输入：`135qqq`
   - 输入完毕后文字瞬间自动替换为：  
     **`本次作业的错题题号为：1，3，5`**！
