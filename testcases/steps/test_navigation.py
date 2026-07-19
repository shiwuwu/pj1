"""页面导航步骤定义。"""

from pathlib import Path
from pytest_bdd import when, then, scenarios

from actions.navigation import navigate_to_page, go_back, wait_for_page
from actions.verify import verify_component_text, verify_page_contains
from testcases.steps.step_patterns import all_of, GENERATED_DIR

for lang_dir in GENERATED_DIR.iterdir() if GENERATED_DIR.exists() else []:
    fp = lang_dir / "navigation.feature"
    if fp.exists():
        scenarios(str(fp))


@when(*all_of("wait_text"))
def step_wait_for_text(driver, comp, text: str):
    wait_for_page(driver, comp, text)


@when(*all_of("wait_id"))
def step_wait_for_id(driver, comp, id: str):
    wait_for_page(driver, comp, id)


@when(*all_of("click_text"))
def step_navigate_to(driver, comp, text: str):
    navigate_to_page(driver, comp, text)


@when(*all_of("go_back"))
def step_go_back(driver, comp):
    go_back(driver)


@then(*all_of("verify_text"))
def step_verify_text(driver, comp, text: str):
    verify_component_text(driver, comp, text)


@then(*all_of("verify_page_contains"))
def step_verify_page_contains(driver, comp, id: str):
    verify_page_contains(driver, comp, id)
