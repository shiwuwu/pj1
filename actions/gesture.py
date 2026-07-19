"""手势操作 —— 滑动、双击、点击。"""

from hypium import UiDriver

from utils.component import ComponentHelper
from utils.logger import get_logger

logger = get_logger(__name__)


def swipe_on_list(driver: UiDriver, comp: ComponentHelper, list_id: str, direction: str = "up"):
    c = comp.find_by_id(list_id)
    c.swipe(direction)


def double_tap_component(driver: UiDriver, comp: ComponentHelper, component_id: str):
    c = comp.find_by_id(component_id)
    c.doubleClick()


def tap_component_by_id(driver: UiDriver, comp: ComponentHelper, component_id: str):
    comp.tap_id(component_id)


def press_enter_key(driver: UiDriver, _comp=None):
    from hypium import KeyCode
    driver.press_key(KeyCode.ENTER)
