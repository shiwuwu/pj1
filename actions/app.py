"""应用操作 —— 启动、后台恢复、回到桌面等。"""

import time

from hypium import UiDriver

from common.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def launch_app(driver: UiDriver, app_id: str, _comp=None):
    """启动应用并等待空闲。"""
    logger.info(f"启动应用: {app_id}")
    driver.start_app(app_id)
    driver.wait_for_idle()
    time.sleep(Config.ACTION_INTERVAL)


def go_to_home(driver: UiDriver, _comp=None):
    """按 Home 键回到桌面。"""
    logger.info("回到桌面")
    driver.go_home()
    time.sleep(Config.ACTION_INTERVAL)


def ensure_app_ready(driver: UiDriver, app_id: str, _comp=None):
    """确保应用已安装可用，否则抛出异常。"""
    if not driver.has_app(app_id):
        raise RuntimeError(f"应用 '{app_id}' 未安装，请检查设备")
    logger.info(f"应用 '{app_id}' 已就绪")
