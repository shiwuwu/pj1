"""应用启动步骤定义。"""

from pathlib import Path
from pytest_bdd import given, when, then, scenarios

from actions.app import launch_app, go_to_home, ensure_app_ready
from actions.verify import verify_app_launched, verify_component_text, verify_component_id
from testcases.steps.step_patterns import all_of, generated_path, GENERATED_DIR

# 加载生成目录下所有语言的 feature
for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "app_launch.feature"
    if fp.exists():
        scenarios(str(fp))


@given(*all_of("device_ready"))
def ensure_device_ready(driver, comp):
    driver.unlock()
    driver.wake_up_display()


@given(*all_of("app_installed"))
def check_app_installed(driver, comp, app_id: str):
    ensure_app_ready(driver, app_id)


@when(*all_of("launch_app"))
@when(*all_of("relaunch_app"))
def step_launch_app(driver, comp, app_id: str):
    launch_app(driver, app_id)


@when(*all_of("go_home"))
def step_go_home(driver, comp):
    go_to_home(driver)


@then(*all_of("app_launched"))
def step_verify_launched(driver, comp):
    verify_app_launched(driver)


@then(*all_of("verify_text"))
def step_verify_text(driver, comp, text: str):
    verify_component_text(driver, comp, text)


@then(*all_of("verify_id"))
def step_verify_id(driver, comp, id: str):
    verify_component_id(driver, comp, id)
