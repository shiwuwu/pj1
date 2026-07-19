"""组件操作封装 —— 简化常用组件查找/操作模式。"""

import time

from hypium import UiDriver, UiComponent, BY, MatchPattern

from common.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class ComponentHelper:
    """对 hypium 组件操作的高级封装。"""

    def __init__(self, driver: UiDriver):
        self._driver = driver

    def find_by_text(self, text: str, match: MatchPattern = MatchPattern.EQUALS) -> UiComponent:
        logger.debug(f"查找组件: text='{text}'")
        return self._driver.find_component(BY.text(text, match))

    def find_by_id(self, cid: str, match: MatchPattern = MatchPattern.EQUALS) -> UiComponent:
        logger.debug(f"查找组件: id='{cid}'")
        return self._driver.find_component(BY.id(cid, match))

    def wait_for_text(self, text: str, timeout: float = 10) -> UiComponent:
        logger.debug(f"等待组件出现: text='{text}'（超时 {timeout}s）")
        return self._driver.wait_for_component(BY.text(text, MatchPattern.EQUALS), timeout)

    def wait_for_id(self, cid: str, timeout: float = 10) -> UiComponent:
        logger.debug(f"等待组件出现: id='{cid}'（超时 {timeout}s）")
        return self._driver.wait_for_component(BY.id(cid, MatchPattern.EQUALS), timeout)

    def tap_text(self, text: str):
        comp = self.find_by_text(text)
        comp.click()
        time.sleep(Config.ACTION_INTERVAL)
        logger.info(f"已点击: text='{text}'")

    def tap_id(self, cid: str):
        comp = self.find_by_id(cid)
        comp.click()
        time.sleep(Config.ACTION_INTERVAL)
        logger.info(f"已点击: id='{cid}'")

    def type_into(self, cid: str, text: str):
        comp = self.find_by_id(cid)
        comp.click()
        comp.inputText(text)
        time.sleep(Config.ACTION_INTERVAL)
        logger.info(f"已输入: id='{cid}' <- '{text}'")

    def assert_exists_text(self, text: str):
        comp = self.find_by_text(text)
        assert comp is not None, f"断言失败: 未找到 text='{text}'"
        logger.info(f"验证通过: text='{text}' 存在")

    def assert_exists_id(self, cid: str):
        comp = self.find_by_id(cid)
        assert comp is not None, f"断言失败: 未找到 id='{cid}'"
        logger.info(f"验证通过: id='{cid}' 存在")
