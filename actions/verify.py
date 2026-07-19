"""验证操作 —— 组件存在性、Toast 消息、应用状态、截图。"""

from hypium import UiDriver

from utils.component import ComponentHelper
from utils.screenshot import ScreenshotHelper

logger = __import__("utils.logger", fromlist=["get_logger"]).get_logger(__name__)


def verify_component_text(driver: UiDriver, comp: ComponentHelper, text: str):
    comp.assert_exists_text(text)


def verify_component_id(driver: UiDriver, comp: ComponentHelper, component_id: str):
    comp.assert_exists_id(component_id)


def verify_page_contains(driver: UiDriver, comp: ComponentHelper, component_id: str):
    comp.assert_exists_id(component_id)


def verify_toast_message(driver: UiDriver, expected_text: str, _comp=None):
    toast = driver.get_latest_toast()
    assert toast is not None, "未收到 Toast 消息"
    assert expected_text in toast, (
        f"Toast 内容不匹配: 预期包含 '{expected_text}'，实际 '{toast}'"
    )


def verify_app_launched(driver: UiDriver, _comp=None):
    assert driver.current_app() is not None, "应用未成功启动"


def verify_search_not_empty(driver: UiDriver, comp: ComponentHelper, result_list_id: str = "search_result_list"):
    comp.assert_exists_id(result_list_id)


def take_screenshot(driver: UiDriver, comp: ComponentHelper, filename: str, screenshot: ScreenshotHelper = None):
    if screenshot:
        screenshot.take(filename)
