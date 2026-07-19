"""搜索操作 —— 关键字搜索、清空历史。"""

from hypium import UiDriver, KeyCode

from utils.component import ComponentHelper
from utils.logger import get_logger

logger = get_logger(__name__)


def open_search(driver: UiDriver, comp: ComponentHelper, search_icon_id: str = "search_icon"):
    """点击搜索图标打开搜索页面。"""
    logger.info("打开搜索页面")
    comp.tap_id(search_icon_id)


def input_search_keyword(driver: UiDriver, comp: ComponentHelper, keyword: str, input_id: str = "search_input"):
    """在搜索框输入关键字。"""
    logger.info(f"输入搜索关键字: '{keyword}'")
    comp.type_into(input_id, keyword)


def submit_search(driver: UiDriver, comp: ComponentHelper):
    """提交搜索（按回车键）。"""
    logger.info("提交搜索")
    driver.press_key(KeyCode.ENTER)


def perform_search(driver: UiDriver, comp: ComponentHelper, keyword: str):
    """完整的搜索流程：打开搜索 → 输入关键字 → 提交。"""
    open_search(driver, comp)
    input_search_keyword(driver, comp, keyword)
    submit_search(driver, comp)


def clear_search_history(driver: UiDriver, comp: ComponentHelper, button_id: str = "clear_history"):
    """清空搜索历史。"""
    logger.info("清空搜索历史")
    comp.tap_id(button_id)
