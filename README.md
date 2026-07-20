# Hypium + pytest-bdd 测试框架

基于 **pytest-bdd**（行为驱动开发）和 **Hypium**（HarmonyOS UI 测试框架）的三层架构自动化测试项目。

## 项目结构

```
pj/
├── common/                             # 公共工具层 —— Driver 管理 & 全局配置
│   ├── __init__.py
│   ├── config.py                       # 环境变量驱动的配置常量
│   └── driver_manager.py              # UiDriver 单例管理器（connect/close）
│
├── config/                              # 配置模块
│   ├── __init__.py
│   └── settings.py                     # 日志抓取、输出路径等默认设置
│
├── utils/                              # 工具文件夹 —— 可复用的测试辅助工具
│   ├── __init__.py
│   ├── logger.py                       # 统一日志（控制台 + 运行时写入 reports/）
│   ├── screenshot.py                   # 截图保存 & 失败自动截图
│   ├── device_utils.py                 # 设备状态检查、应用管理
│   ├── component.py                    # 组件查找/操作的高级封装
│   └── report.py                       # 自定义 HTML Summary 报告
│
├── tools/                              # 工具模块
│   ├── __init__.py
│   └── harmony_log.py                 # 鸿蒙设备日志抓取工具（hdc hilog）
│
├── actions/                            # 业务动作封装层 —— 可复用的业务方法
│   ├── __init__.py
│   ├── app.py                          # 应用操作: launch / go_home / ensure_ready
│   ├── navigation.py                   # 导航操作: navigate / go_back / wait
│   ├── search.py                       # 搜索操作: search / input / submit / clear
│   ├── gesture.py                      # 手势操作: swipe / double_tap / press_key
│   └── verify.py                       # 验证操作: component / toast / screenshot
│
├── testcases/                          # 用例文件夹
│   ├── __init__.py
│   ├── features/                       # Gherkin 模板（@key("arg") 语法）
│   │   ├── app_launch.feature          # 应用启动与首页验证（2 个场景）
│   │   ├── navigation.feature          # 页面导航与跳转（3 个场景）
│   │   ├── search.feature              # 搜索功能（2 个场景）
│   │   ├── gesture.feature             # 手势与滑动操作（3 个场景）
│   │   └── .generated/                 # 自动生成的多语言 feature 文件（不提交 git）
│   │       ├── zh_CN/
│   │       ├── zh_TW/
│   │       └── en/
│   └── steps/                          # 步骤定义（Step Definitions）
│       ├── __init__.py
│       ├── conftest.py                 # Fixture 工厂 + pytest-bdd 钩子
│       ├── step_patterns.py            # 多语言模板引擎 + all_of() 解析器
│       ├── test_app_launch.py
│       ├── test_navigation.py
│       ├── test_search.py
│       └── test_gesture.py
│
├── locales/                            # 国际化翻译
│   ├── zh_CN.json                      # 简体中文
│   ├── zh_TW.json                      # 繁体中文
│   └── en.json                         # 英语
│
├── ui/                                 # 可视化界面（customtkinter）
│   ├── __init__.py
│   ├── main_window.py                  # 主窗口 —— 设备/用例列表/控制/日志
│   └── test_runner.py                  # 后台线程执行 pytest + 实时输出
│
├── run_ui.py                           # GUI 启动入口
├── reports/                            # 测试报告 + 运行日志（自动生成）
├── logs/                               # 鸿蒙设备日志抓取输出（自动生成）
├── screenshots/                        # 截图输出目录（自动生成）
├── pytest.ini
└── README.md
```

## 架构设计

```
                         ┌──────────────────────────────────┐
                         │    testcases/features/*.feature   │  ← 业务场景（模板，@key 语法）
                         │    locales/*.json （翻译）         │
                         │         ↓ generate_features()     │
                         │    .generated/{lang}/*.feature     │  ← 运行时加载
                         └──────────────┬───────────────────┘
                                        │ scenarios() 注册
                                        ▼
                         ┌──────────────────────────────────┐
                         │      testcases/steps/             │  ← 步骤映射层（薄层）
                         │  test_*.py                        │     @given / @when / @then
                         │  step_patterns.py (all_of 多语言)  │
                         │  conftest.py (fixture 工厂)        │
                         └──────────────┬───────────────────┘
                                        │ 调用业务方法
                                        ▼
                         ┌──────────────────────────────────┐
                         │        actions/                   │  ← 业务动作封装层
                         │  app / navigation /               │     把零散 hypium 调用
                         │  search / gesture / verify        │     组合为可复用业务方法
                         └──────┬───────────────┬───────────┘
                                │               │
                    ┌───────────┘               └───────────┐
                    ▼                                       ▼
        ┌──────────────────────┐             ┌──────────────────────┐
        │      common/         │             │       utils/         │
        │  DriverManager       │             │  ComponentHelper     │
        │  Config              │             │  ScreenshotHelper    │
        └──────────┬───────────┘             │  device_utils        │
                   │                         │  logger              │
                   │                         └──────────┬───────────┘
                   │                                    │
                   └──────────────┬─────────────────────┘
                                  ▼
                    ┌──────────────────────────┐
                    │    hypium.UiDriver        │  ← 底层驱动
                    │    HarmonyOS 设备通信      │
                    └──────────────────────────┘
```

### 各层职责

| 层级 | 目录 | 职责 | 依赖方向 |
|------|------|------|----------|
| **场景层** | `testcases/features/` | Gherkin 模板 + 多语言翻译 | → locales |
| **步骤层** | `testcases/steps/` | 解析 Gherkin 参数，转调 actions 方法 | → actions |
| **动作层** | `actions/` | 把 hypium 零散调用组合为业务方法 | → common, utils |
| **工具层** | `utils/` | 可复用的测试辅助（组件封装、截图、日志、设备检查） | → hypium |
| **公共层** | `common/` | Driver 生命周期管理、全局配置常量 | → hypium |

## 多语言支持

Feature 文件使用 `@key("arg")` 模板语法，通过 `step_patterns.py` 渲染为具体语言的 `.feature` 文件：

```
testcases/features/app_launch.feature  (模板)
    @launch_app("com.example.app")
         ↓ generate_features("en")
    When launch application "com.example.app"   (.generated/en/)
         ↓ generate_features("zh_CN")  
    When 启动应用 "com.example.app"              (.generated/zh_CN/)
```

23 个公共步骤定义在所有三种语言中共享，通过 `all_of("key")` 自动匹配。

## 日志

| 场景 | 控制台 | 文件 | 位置 |
|---|---|---|---|
| UI 空闲时 | ✓ | ✗ | — |
| 运行测试时 | ✓ | ✓ | `reports/test_log_<时间戳>.log` |
| 测试结束后 | ✓ | ✗ | — |

日志文件与 HTML 报告放在同一个 `reports/` 目录下。

## 鸿蒙设备日志抓取

```python
from tools import HarmonyLogCapture

cap = HarmonyLogCapture(device_sn="xxx")
cap.save_to_file("crash.log", duration=5, level="E")   # 抓 5 秒 Error 日志
cap.stream(callback=lambda line: print(line))            # 实时抓取
cap.stop()
```

## 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| `hypium` | 6.1.0.210 | HarmonyOS UI 自动化驱动 |
| `pytest-bdd` | 8.1.0 | Gherkin BDD 测试框架 |
| `pytest` | — | 测试运行器 |
| `customtkinter` | ≥6.0 | GUI 界面 |

安装：

```bash
pip install hypium pytest-bdd customtkinter
```

## 快速开始

### 1. 连接设备

```bash
hdc list targets
```

### 2. 运行测试

#### 命令行

```bash
# 全部测试
pytest testcases/ -v -s

# 指定语言
TEST_LANG=zh_CN pytest testcases/ -v -s

# 指定设备
HARMONY_DEVICE_SN=ABC123 pytest testcases/
```

#### 可视化界面（推荐）

```bash
python run_ui.py
```

**GUI 功能：**
- 设备连接管理（输入 SN 一键连接）
- 用例列表（Feature 级别，按语言过滤）
- 运行全部 / 运行选中
- 实时彩色日志输出（通过=绿色，失败=红色）
- 执行结果图标（✓ / ✗）
- 测试统计（总数/通过/失败）
- 手动停止测试
- 📊 一键查看 HTML 报告

## 添加新用例

使用 `/add-testcase` 技能快速添加，或按以下步骤手动操作：

### 步骤 1：在 locales 中添加翻译

```json
// locales/zh_CN.json
{ "enter_username": "在 \"{input_id}\" 中输入用户名 \"{username}\"" }
// locales/en.json
{ "enter_username": "enter username \"{username}\" into \"{input_id}\"" }
```

### 步骤 2：创建 Feature 模板

```gherkin
# testcases/features/login.feature
Feature: 用户登录
    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: 密码登录
        When @launch_app("com.example.app")
        And @enter_username("login_input", "admin")
        And @click_id("submit_btn")
        Then @verify_text("欢迎")
```

### 步骤 3：创建 actions 业务方法

```python
# actions/login.py
from utils.logger import get_logger
logger = get_logger(__name__)

def enter_username(driver, comp, input_id: str, username: str):
    logger.info(f"输入用户名: {username}")
    comp.type_into(input_id, username)
```

### 步骤 4：创建步骤定义

```python
# testcases/steps/test_login.py
from pytest_bdd import when, scenarios
from actions.login import enter_username
from testcases.steps.step_patterns import all_of, GENERATED_DIR

for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "login.feature"
    if fp.exists():
        scenarios(str(fp))

@when(*all_of("enter_username"))
def step_enter_username(driver, comp, input_id: str, username: str):
    enter_username(driver, comp, input_id, username)
```

### 步骤 5：注册并生成

在 `actions/__init__.py` 中添加导出，然后运行：

```python
from testcases.steps.step_patterns import generate_features
generate_features("zh_CN"); generate_features("en"); generate_features("zh_TW")
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HARMONY_DEVICE_SN` | 目标设备序列号 | 空 |
| `HARMONY_IMPLICIT_WAIT` | 隐式等待超时（秒） | 10 |
| `HARMONY_ACTION_INTERVAL` | 操作间隔（秒） | 1.0 |
| `HARMONY_SCREENSHOT_DIR` | 截图保存目录 | `./screenshots/` |
| `HARMONY_LOG_DIR` | 日志目录 | `./logs/` |
| `HARMONY_LOG_FILE` | 运行时日志文件路径 | 自动生成于 `reports/` |
| `HDC_PATH` | hdc 可执行文件路径 | `hdc` |
| `TEST_LANG` | 测试语言（zh_CN/zh_TW/en/all） | `zh_CN` |
