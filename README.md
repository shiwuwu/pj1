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
├── utils/                              # 工具文件夹 —— 可复用的测试辅助工具
│   ├── __init__.py
│   ├── logger.py                       # 统一日志输出
│   ├── screenshot.py                   # 截图保存 & 失败自动截图
│   ├── device_utils.py                 # 设备状态检查、应用管理
│   └── component.py                    # 组件查找/操作的高级封装
│
├── actions/                            # 业务动作封装层 —— 可复用的业务方法
│   ├── __init__.py
│   ├── app.py                          # 应用操作: 启动/停止/重启/回桌面
│   ├── navigation.py                   # 导航操作: 跳转/Tab切换/返回/等待
│   ├── search.py                       # 搜索操作: 输入/提交/清空历史
│   ├── gesture.py                      # 手势操作: 滑动/双击/返回手势/点击
│   └── verify.py                       # 验证操作: 组件/Toast/截图/状态
│
├── testcases/                          # 用例文件夹 —— 所有测试内容
│   ├── __init__.py
│   ├── features/                       # Gherkin 场景描述（按模块拆分）
│   │   ├── __init__.py
│   │   ├── app_launch.feature          # 应用启动与首页验证（2 个场景）
│   │   ├── navigation.feature          # 页面导航与跳转（3 个场景）
│   │   ├── search.feature              # 搜索功能（2 个场景）
│   │   └── gesture.feature             # 手势与滑动操作（3 个场景）
│   └── steps/                          # 步骤定义（Step Definitions）
│       ├── __init__.py
│       ├── conftest.py                 # Fixture 工厂 + pytest-bdd 钩子
│       ├── test_app_launch.py          # 启动相关步骤
│       ├── test_navigation.py          # 导航相关步骤
│       ├── test_search.py             # 搜索相关步骤
│       └── test_gesture.py            # 手势相关步骤
│
├── ui/                                 # 可视化界面（Tkinter, Win/Mac 通用）
│   ├── __init__.py
│   ├── main_window.py                  # 主窗口 —— 设备/用例树/控制/日志
│   └── test_runner.py                  # 后台线程执行 pytest + 实时输出
│
├── run_ui.py                           # GUI 启动入口
├── screenshots/                        # 截图输出目录（自动创建）
├── pytest.ini
└── README.md
```

## 架构设计

```
                         ┌──────────────────────────────────┐
                         │        testcases/features/        │  ← 业务场景（Gherkin）
                         │  app_launch / navigation /        │
                         │  search / gesture .feature        │
                         └──────────────┬───────────────────┘
                                        │ scenarios() 注册
                                        ▼
                         ┌──────────────────────────────────┐
                         │      testcases/steps/             │  ← 步骤映射层（薄层）
                         │  test_*.py                        │     只做参数解析 + 调用 actions
                         │  @given / @when / @then           │
                         │  conftest.py (fixture 工厂)        │
                         └──────────────┬───────────────────┘
                                        │ 调用业务方法
                                        ▼
                         ┌──────────────────────────────────┐
                         │        actions/                   │  ← 业务动作封装层 ★
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
| **场景层** | `testcases/features/` | Gherkin 自然语言描述测试意图 | 无依赖 |
| **步骤层** | `testcases/steps/` | 解析 Gherkin 参数，转调 actions 方法 | → actions |
| **动作层** ★ | `actions/` | 把 hypium 零散调用组合为业务方法，可被多个 step 复用 | → common, utils |
| **工具层** | `utils/` | 可复用的测试辅助（组件封装、截图、日志、设备检查） | → hypium |
| **公共层** | `common/` | Driver 生命周期管理、全局配置常量 | → hypium |

### actions 层方法一览

| 模块 | 方法 | 说明 |
|------|------|------|
| `app` | `launch_app` / `restart_app` / `stop_app` / `go_to_home` / `ensure_app_ready` | 应用生命周期管理 |
| `navigation` | `navigate_to_page` / `switch_tab` / `go_back` / `wait_for_page` | 页面跳转与等待 |
| `search` | `perform_search` / `open_search` / `input_search_keyword` / `submit_search` / `clear_search_history` | 完整搜索流程 |
| `gesture` | `swipe_on_list` / `double_tap_component` / `perform_back_gesture` / `tap_component_by_id` / `swipe_up/down_on_component` | 手势操作 |
| `verify` | `verify_component_text/id` / `verify_page_contains` / `verify_toast_message` / `verify_app_launched` / `verify_search_not_empty` / `take_screenshot` | 断言验证 |

### HTML 报告

框架支持两种 HTML 报告输出：

| 报告类型 | 生成方式 | 说明 |
|----------|----------|------|
| **pytest-html 标准报告** | 自动生成（GUI / CLI `--html`） | pytest 官方报告插件 |
| **自定义 Summary 报告** | `utils/report.py` → `generate_summary_report()` | 独立的、美观的汇总报告 |

**CLI 运行并生成报告：**

```bash
pytest testcases/ --html=reports/report.html --self-contained-html
```

**GUI 运行：**
- 点击 "运行全部" / "运行选中" → 自动生成两种报告到 `reports/` 目录
- 测试完成后 "📊 查看报告" 按钮自动启用
- 点击可在浏览器中查看报告

报告包含：
- 总计/通过/失败/通过率 统计卡片
- Feature → Scenario 明细表格
- 失败项错误信息
- 进度条可视化

## 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| `hypium` | 6.1.0.210 | HarmonyOS UI 自动化驱动 |
| `pytest-bdd` | 8.1.0 | Gherkin BDD 测试框架 |
| `pytest` | — | 测试运行器 |

安装：

```bash
pip install hypium pytest-bdd
```

## 快速开始

### 1. 连接设备

确保 HarmonyOS/OpenHarmony 设备通过 USB 连接，且 hdc 可用：

```bash
hdc list targets
```

### 2. 运行测试

#### 命令行方式

```bash
# 运行全部 BDD 测试
pytest testcases/

# 指定设备 SN
HARMONY_DEVICE_SN=ABC123 pytest testcases/

# 运行特定 feature（按文件名过滤）
pytest testcases/ -k "navigation"

# 运行特定场景（按场景名过滤）
pytest testcases/ -k "Toast 消息验证"

# 详细输出 + 不截断
pytest testcases/ -v -s
```

#### 可视化界面方式（推荐）

```bash
python run_ui.py
```

GUI 功能：

```
┌──────────────────────────────────────────────┐
│  HarmonyOS UI Test Runner                    │
├──────────────┬───────────────────────────────┤
│ 设备连接      │  输出日志                      │
│  SN: [____]  │  ┌───────────────────────────┐│
│  [连接]       │  │ test session starts       ││
│ 状态: 已连接  │  │ PASSED test_xxx           ││
│              │  │                           ││
│ 测试用例      │  │                           ││
│  ▼ 应用启动   │  └───────────────────────────┘│
│    - 冷启动   │                               │
│    - 后台恢复 │                               │
│  ▼ 页面导航   │                               │
│    - Tab 切换 │                               │
│    - 返回操作 │                               │
│              │                               │
│ [▶ 运行全部]  │                               │
│ [▶ 运行选中]  │                               │
│ [■ 停止]      │                               │
│ [==========] │                               │
├──────────────┴───────────────────────────────┤
│ 共 10 个测试 | 通过 8 | 失败 2                 │
└──────────────────────────────────────────────┘
```

**GUI 特性：**
- 设备连接管理（输入 SN 一键连接）
- Feature/Scenario 树形列表（自动从 `.feature` 文件扫描）
- 运行全部 / 运行选中场景
- 实时彩色日志输出（通过=绿色，失败=红色）
- 场景执行结果图标（✓ / ✗）
- 测试统计（总数/通过/失败）
- 手动停止测试
- 零额外依赖（Win 和 Mac 内置 Tkinter）

### 3. 跳过场景

在 `.feature` 文件中对场景标记 `@skip`：

```gherkin
@skip
Scenario: 这个场景会被跳过
    ...
```

## 添加新用例

### 步骤 1：在 actions 层写好业务方法（可复用）

```python
# actions/login.py —— 新增登录模块
from hypium import UiDriver
from utils.component import ComponentHelper
from utils.logger import get_logger

logger = get_logger(__name__)


def perform_login(driver: UiDriver, comp: ComponentHelper, username: str, password: str):
    """完整的登录流程：点击登录入口 → 输入账号密码 → 提交。"""
    logger.info(f"执行登录: user='{username}'")
    comp.tap_id("login_btn")
    comp.type_into("username", username)
    comp.type_into("password", password)
    comp.tap_id("submit")
```

### 步骤 2：在 Gherkin 中组合已有步骤

```gherkin
# testcases/features/login.feature
Feature: 用户登录
    Background:
        Given 设备已连接且屏幕已解锁
        And 目标应用 "com.example.app" 已安装

    Scenario: 密码登录成功
        When 启动应用 "com.example.app"
        And 点击组件 id "login_btn"
        And 在 id "username" 中输入文本 "admin"
        And 在 id "password" 中输入文本 "123456"
        And 点击组件 id "submit"
        Then 验证组件存在 text "欢迎回来"
```

### 步骤 3：仅需一行注册（已有步骤自动复用）

```python
# testcases/steps/test_login.py
from pathlib import Path
from pytest_bdd import scenarios

FEATURE_DIR = Path(__file__).resolve().parent.parent / "features"
scenarios(str(FEATURE_DIR / "login.feature"))
```

**关键设计**：step 文件只做参数映射 → actions 层写业务逻辑。同一个 action 方法可以被 Gherkin 中不同步骤组合出来的场景反复复用，不需要重复写代码。

## Hypium 常用 API 速查

### UiDriver — 设备操作

| 方法 | 说明 |
|------|------|
| `driver.connect(sn)` | 连接指定设备 |
| `driver.start_app(id)` | 启动应用 |
| `driver.stop_app(id)` | 停止应用 |
| `driver.go_back()` | 返回 |
| `driver.go_home()` | 回桌面 |
| `driver.press_key(code)` | 按键 |
| `driver.swipe(dir)` | 滑动 |
| `driver.take_screenshot(path)` | 截图 |
| `driver.get_latest_toast()` | 获取最新 Toast |
| `driver.unlock()` | 解锁 |

### BY — 组件选择器

| 选择器 | 说明 |
|--------|------|
| `BY.text("首页")` | 按文本（默认 CONTAINS） |
| `BY.text("首页", MatchPattern.EQUALS)` | 精确匹配 |
| `BY.id("search_btn")` | 按 ID |
| `BY.type("Button")` | 按类型 |
| `BY.description("搜索")` | 按无障碍描述 |
| `BY.xpath("//Button[@id='x']")` | XPath |

### UiComponent — 组件操作

| 方法 | 说明 |
|------|------|
| `comp.click()` / `doubleClick()` / `longClick()` | 点击/双击/长按 |
| `comp.inputText(t)` / `clearText()` | 输入/清空 |
| `comp.getText()` | 获取文本 |
| `comp.swipe(dir)` | 组件内滑动 |
| `comp.scrollToTop()` / `scrollToBottom()` | 滚动 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HARMONY_DEVICE_SN` | 目标设备序列号 | 空（自动） |
| `HARMONY_IMPLICIT_WAIT` | 隐式等待超时（秒） | 10 |
| `HARMONY_ACTION_INTERVAL` | 操作间隔（秒） | 1.0 |
| `HARMONY_SCREENSHOT_DIR` | 截图保存目录 | `./screenshots/` |
