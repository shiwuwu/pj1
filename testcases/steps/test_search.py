"""搜索功能步骤定义。"""

from pathlib import Path
from pytest_bdd import when, then, scenarios

from actions.gesture import tap_component_by_id, press_enter_key
from actions.verify import verify_search_not_empty, take_screenshot
from testcases.steps.step_patterns import all_of, GENERATED_DIR

for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "search.feature"
    if fp.exists():
        scenarios(str(fp))


@when(*all_of("wait_id"))
def step_wait_id(driver, comp, id: str):
    from actions.navigation import wait_for_page
    wait_for_page(driver, comp, id)


@when(*all_of("click_id"))
def step_tap_id(driver, comp, id: str):
    tap_component_by_id(driver, comp, id)


@when(*all_of("type_into"))
def step_type_into_id(driver, comp, screenshot, id: str, text: str):
    comp.type_into(id, text)


@when(*all_of("press_enter"))
def step_press_enter(driver, comp):
    press_enter_key(driver)


@then(*all_of("search_not_empty"))
def step_verify_results(driver, comp):
    verify_search_not_empty(driver, comp)


@then(*all_of("screenshot"))
def step_take_screenshot(driver, comp, screenshot, filename: str):
    take_screenshot(driver, comp, filename, screenshot)
