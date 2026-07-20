---
name: add-testcase
description: Add a new test case (feature + steps + actions + locale entries)
---

# Add Test Case Skill

Guide for adding a new BDD test case to this HarmonyOS UI Test Framework.

## Project Layering

```
.feature template    →  testcases/features/{module}.feature   (@key("arg") syntax)
       ↓ rendered by step_patterns.py
.generated/{lang}/   →  testcases/features/.generated/{lang}/{module}.feature
       ↓ loaded by pytest-bdd
step definitions     →  testcases/steps/test_{module}.py       (@given/@when/@then)
       ↓ calls
action functions     →  actions/{module}.py                    (business logic)
       ↓ uses
utils/common         →  ComponentHelper, DriverManager, etc.
```

## Step-by-Step Process

### Step 1: Identify what's needed

Ask the user:
- What is the feature (module) name? (e.g., "login", "settings", "notification")
- What scenarios should it test? (describe each scenario briefly)
- What new actions are needed beyond the existing ones?

**Existing reusable actions** (no need to recreate):
- `launch_app`, `go_to_home`, `ensure_app_ready` (from `actions/app.py`)
- `navigate_to_page`, `go_back`, `wait_for_page` (from `actions/navigation.py`)
- `open_search`, `input_search_keyword`, `submit_search`, `perform_search`, `clear_search_history` (from `actions/search.py`)
- `swipe_on_list`, `double_tap_component`, `tap_component_by_id`, `press_enter_key` (from `actions/gesture.py`)
- `verify_component_text`, `verify_component_id`, `verify_page_contains`, `verify_toast_message`, `verify_app_launched`, `take_screenshot` (from `actions/verify.py`)

**Existing locale keys** (23 keys shared across all 3 languages):
`device_ready`, `app_installed`, `launch_app`, `relaunch_app`, `app_launched`, `go_home`, `verify_text`, `verify_id`, `wait_text`, `wait_id`, `click_text`, `click_id`, `go_back`, `verify_page_contains`, `type_into`, `press_enter`, `search_not_empty`, `screenshot`, `swipe_up`, `swipe_down`, `double_tap`, `toast_contains`

### Step 2: Add locale entries (if new @keys needed)

For each **new** step pattern (not in the existing 23 keys), add entries to ALL 3 locale files:

**File:** `locales/zh_CN.json`
**File:** `locales/zh_TW.json`
**File:** `locales/en.json`

Format:
```json
{
    "my_action": "localized step text with {param1} and {param2}"
}
```

Rules:
- Key: `snake_case` identifier
- Value: Gherkin step text with `{placeholder}` for parameters
- The order of `{placeholder}` in the locale string determines the order of arguments in `@key("arg1", "arg2")`

### Step 3: Create the feature template

**File:** `testcases/features/{module}.feature`

Template:
```gherkin
Feature: {中文名称}
    {一句描述}

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: {场景1名称}
        When @some_action("arg1")
        Then @verify_text("预期文本")

    Scenario: {场景2名称}
        Given @launch_app("com.example.app")
        When @some_other_action
        Then @verify_id("expected_id")
        And @screenshot("{filename}")
```

Rules:
- Use `@key` for no-argument steps, `@key("arg1", "arg2")` for parameterized steps
- Arguments are double-quoted strings, comma-separated
- Background is always the same 2 lines
- `@key` names MUST match keys in all 3 locale JSON files

### Step 4: Create action functions

**File:** `actions/{module}.py`

Template:
```python
"""模块说明"""

import time
from hypium import UiDriver
from utils.component import ComponentHelper
from utils.logger import get_logger
from common.config import Config

logger = get_logger(__name__)


def my_action(driver: UiDriver, comp: ComponentHelper, param: str):
    """执行某个操作"""
    logger.info(f"执行操作: {param}")
    comp.tap_text(param)
    driver.wait_for_idle()
    time.sleep(Config.ACTION_INTERVAL)


def another_action(driver: UiDriver):
    """执行另一个操作"""
    logger.info("执行另一个操作")
    driver.press_back()
    time.sleep(Config.ACTION_INTERVAL)
```

Rules:
- `driver: UiDriver` is always the first parameter
- `comp: ComponentHelper` is the second parameter if component operations are needed
- Use `logger.info()` for logging (not `print`)
- Respect `Config.ACTION_INTERVAL` for timing
- One function = one responsibility

### Step 5: Register actions

**File:** `actions/__init__.py`

Add the import line:
```python
from actions.{module} import my_action, another_action
```

### Step 6: Create step definitions

**File:** `testcases/steps/test_{module}.py`

Template:
```python
from pytest_bdd import given, when, then, scenarios
from actions.{module} import my_action, another_action
from testcases.steps.step_patterns import all_of, GENERATED_DIR

# Load generated feature files
for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "{module}.feature"
    if fp.exists():
        scenarios(str(fp))


@when(*all_of("my_action"))
def step_my_action(driver, comp, param: str):
    my_action(driver, comp, param)


@when(*all_of("another_action"))
def step_another_action(driver, comp):
    another_action(driver)
```

Rules:
- Function naming: `step_<verb>_<noun>` (e.g., `step_open_settings`)
- Parameters: `driver` and `comp` come first (pytest fixtures), then keyword params from `{placeholder}` in locale strings
- Type annotations: always add `: str` for string parameters
- The `scenarios()` loop must reference the correct `{module}.feature` filename

### Step 7: Generate feature files

Run the feature generator:
```python
from testcases.steps.step_patterns import generate_features
generate_features("zh_CN")
generate_features("zh_TW")
generate_features("en")
```

Or via pytest (the conftest.py does this automatically based on `TEST_LANG`).

### Step 8: Verify

```bash
# Check that feature files were generated
ls testcases/features/.generated/*/my_module.feature

# Run the specific feature
pytest testcases/steps/test_my_module.py -v -s
```

## File Checklist for Each New Module

| # | File | Action |
|---|---|---|
| 1 | `locales/zh_CN.json` | Add new keys |
| 2 | `locales/zh_TW.json` | Add new keys (same keys, translated) |
| 3 | `locales/en.json` | Add new keys (same keys, translated) |
| 4 | `testcases/features/{module}.feature` | Create template |
| 5 | `actions/{module}.py` | Create action functions |
| 6 | `actions/__init__.py` | Add imports |
| 7 | `testcases/steps/test_{module}.py` | Create step definitions |
| 8 | Run `generate_features()` | Generate language-specific feature files |

## Example: Adding a "Login" module

**User says:** "我想添加登录功能的测试用例"

**locales/zh_CN.json** (add):
```json
{
    "enter_username": "在用户名字段 \"{input_id}\" 中输入 \"{username}\"",
    "enter_password": "在密码字段 \"{input_id}\" 中输入密码",
    "click_login": "点击登录按钮 \"{button_id}\"",
    "verify_login_success": "验证登录成功，页面包含 \"{text}\""
}
```

**testcases/features/login.feature:**
```gherkin
Feature: 登录功能
    验证用户登录流程

    Background:
        Given @device_ready
        And @app_installed("com.example.app")

    Scenario: 正常登录
        When @launch_app("com.example.app")
        And @enter_username("login_username_input", "testuser")
        And @enter_password("login_password_input")
        And @click_login("login_button")
        Then @verify_login_success("首页")
```

**actions/login.py:**
```python
def enter_username(driver, comp, input_id: str, username: str):
    logger.info(f"输入用户名: {username}")
    comp.type_into(input_id, username)

def enter_password(driver, input_id: str):
    logger.info("输入密码")
    driver.input_text(input_id, "test_password")

def click_login(driver, comp, button_id: str):
    logger.info(f"点击登录: {button_id}")
    comp.tap_id(button_id)
```

**testcases/steps/test_login.py:**
```python
from pytest_bdd import given, when, then, scenarios
from actions.login import enter_username, enter_password, click_login
from testcases.steps.step_patterns import all_of, GENERATED_DIR

for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "login.feature"
    if fp.exists():
        scenarios(str(fp))

@when(*all_of("enter_username"))
def step_enter_username(driver, comp, input_id: str, username: str):
    enter_username(driver, comp, input_id, username)

@when(*all_of("enter_password"))
def step_enter_password(driver, comp, input_id: str):
    enter_password(driver, input_id)

@when(*all_of("click_login"))
def step_click_login(driver, comp, button_id: str):
    click_login(driver, comp, button_id)

@then(*all_of("verify_login_success"))
def step_verify_login_success(driver, comp, text: str):
    from actions.verify import verify_component_text
    verify_component_text(driver, comp, text)
```
