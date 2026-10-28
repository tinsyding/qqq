# 错题快速转换助手 - 安卓端

Windows 版错题快速转换助手的 Android 原生移植版本，基于 Kotlin 与 Android 无障碍服务（AccessibilityService）开发。在手机端各输入场景（微信、QQ、钉钉、备忘录等）中，键入如 `135qqq` 后可自动退格并展开为预设文案。

## 功能特点

1. **无障碍自动展开**
   - 兼容各类第三方及系统自带输入法。
   - 输入数字后键入触发后缀（如 `135qqq` 或 `1 3 12qqq`），自动退格并替换为预设文案（如 `本次作业的错题题号为：1，3，5`）。
2. **系统划选文本替换（Process Text）**
   - 长按选中文本框内的数字，在系统浮动菜单中选择「转为错题格式」即可就地替换。
3. **配置与自定义**
   - 自定义触发词（如 `qqq`、`..`、`fff` 等）。
   - 自定义文案模板（支持 `{nums}` 占位符）与预设切换。
   - 自定义题号分隔符（中文逗号、顿号、空格等）。
   - 内置测试预览与一键复制功能。

## 项目结构

```text
android_app/
│
├── app/
│   ├── build.gradle.kts           # App 模块依赖与构建配置
│   ├── src/
│   │   ├── main/
│   │   │   ├── AndroidManifest.xml # 核心清单文件（声明无障碍服务与文本处理 Activity）
│   │   │   ├── java/com/transcriber/homework/
│   │   │   │   ├── MainActivity.kt        # 设置主界面
│   │   │   │   ├── ProcessTextActivity.kt # 划选文本快捷替换 Activity
│   │   │   │   ├── core/
│   │   │   │   │   ├── TextProcessor.kt   # 数字切分与模板格式化逻辑
│   │   │   │   │   └── ConfigManager.kt   # 本地持久化配置管理
│   │   │   │   └── service/
│   │   │   │       └── TextExpanderService.kt # 无障碍文本监听与替换服务
│   │   │   └── res/                       # 资源文件（布局、色彩、无障碍配置）
│   │   └── test/                          # 核心算法单元测试
│
├── autoxjs/                               # AutoX.js 脚本方案
│   └── 错题转换助手.js
│
├── build.gradle.kts                       # 根工程构建配置
├── settings.gradle.kts                    # 工程设置
└── README.md
```

## 构建与安装

### 方式 1：使用 Android Studio 构建

1. 使用 Android Studio 打开 `android_app` 目录。
2. 等待 Gradle 同步完成。
3. 连接设备或启动模拟器，点击 **Run ('app')** 部署安装；或执行 **Build -> Build Bundle(s) / APK(s) -> Build APK(s)**，在 `app/build/outputs/apk/debug/` 目录下生成 `app-debug.apk`。

### 方式 2：使用 AutoX.js 运行 / 打包

1. 手机安装 [AutoX.js](https://github.com/kkevsekk1/AutoX)。
2. 将 `autoxjs/错题转换助手.js` 导入 AutoX.js。
3. 在 AutoX.js 中直接运行脚本，或使用内置打包功能生成独立安装包。

## 使用步骤

1. 安装并启动 App。
2. 按照界面提示进入系统「无障碍 / 辅助功能」设置页，开启「错题快速转换助手 - 自动展开服务」。
3. 在任意文本输入框中键入数字加后缀（如 `135qqq`），即可自动转换为设定文案。
