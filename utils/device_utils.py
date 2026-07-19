"""设备工具函数 —— 设备状态检查等辅助操作。"""

from hypium import UiDriver

from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_screen_on(driver: UiDriver):
    driver.wake_up_display()
    logger.info("屏幕已唤醒")


def ensure_unlocked(driver: UiDriver):
    driver.unlock()
    logger.info("屏幕已解锁")
