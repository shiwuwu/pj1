"""导航操作 —— 页面跳转、返回、等待。"""

import time

from hypium import UiDriver

from common.config import Config
from utils.component import ComponentHelper
from utils.logger import get_logger

logger = get_logger(__name__)


def navigate_to_page(driver: UiDriver, comp: ComponentHelper, target_text: str):
    logger.info(f"导航到: '{target_text}'")
    comp.tap_text(target_text)


def go_back(driver: UiDriver, _comp=None):
    logger.info("返回上一页")
    driver.go_back()
    time.sleep(Config.ACTION_INTERVAL)


def wait_for_page(driver: UiDriver, comp: ComponentHelper, text: str):
    logger.info(f"等待页面加载: text='{text}'")
    comp.wait_for_text(text)
