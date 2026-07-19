"""手势操作步骤定义。"""

from pathlib import Path
from pytest_bdd import when, then, scenarios

from actions.gesture import swipe_on_list, double_tap_component, tap_component_by_id
from actions.verify import verify_toast_message, verify_component_id, take_screenshot
from testcases.steps.step_patterns import all_of, GENERATED_DIR

for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "gesture.feature"
    if fp.exists():
        scenarios(str(fp))


@when(*all_of("swipe_up"))
def step_swipe_up(driver, comp, id: str):
    swipe_on_list(driver, comp, id, "up")


@when(*all_of("swipe_down"))
def step_swipe_down(driver, comp, id: str):
    swipe_on_list(driver, comp, id, "down")


@when(*all_of("double_tap"))
def step_double_tap(driver, comp, id: str):
    double_tap_component(driver, comp, id)


@when(*all_of("click_id"))
def step_tap_by_id(driver, comp, id: str):
    tap_component_by_id(driver, comp, id)


@then(*all_of("toast_contains"))
def step_verify_toast(driver, comp, text: str):
    verify_toast_message(driver, text)


@then(*all_of("verify_id"))
def step_verify_id(driver, comp, id: str):
    verify_component_id(driver, comp, id)


@then(*all_of("screenshot"))
def step_screenshot(driver, comp, screenshot, filename: str):
    take_screenshot(driver, comp, filename, screenshot)
