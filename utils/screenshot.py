"""截图工具 —— 封装截图保存与目录管理。"""

import os
from datetime import datetime
from pathlib import Path

from hypium import UiDriver

from common.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotHelper:
    def __init__(self, driver: UiDriver, base_dir: str | None = None):
        self._driver = driver
        self._base_dir = Path(base_dir or Config.SCREENSHOT_DIR)

    def take(self, filename: str, subdir: str = "") -> str:
        """截图并保存，返回文件路径。

        自动创建以日期命名的子目录，文件名追加时间戳避免覆盖。
        """
        path = self._base_dir / subdir
        path.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_name = f"{filename}_{ts}.png"
        full_path = path / full_name

        self._driver.take_screenshot(str(full_path))
        logger.info(f"截图已保存: {full_path}")
        return str(full_path)

    def take_on_fail(self, scenario_name: str):
        """失败时自动截图到 failures/ 子目录。"""
        safe_name = scenario_name.replace(" ", "_").replace("/", "_")
        return self.take(f"FAIL_{safe_name}", subdir="failures")
