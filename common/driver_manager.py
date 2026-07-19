"""UiDriver 单例管理器 —— 整个测试会话共享一个连接。"""

from hypium import UiDriver

from common.config import Config


class DriverManager:
    """管理 hypium UiDriver 的生命周期。

    用法:
        dm = DriverManager()
        dm.connect()
        dm.driver.click(...)
        dm.close()
    """

    def __init__(self):
        self._driver: UiDriver | None = None

    @property
    def driver(self) -> UiDriver:
        if self._driver is None:
            raise RuntimeError("Driver 未连接，请先调用 connect()")
        return self._driver

    def connect(self, device_sn: str | None = None) -> UiDriver:
        """连接设备，优先使用传入 SN，其次使用 Config 中的配置。"""
        sn = device_sn or Config.DEVICE_SN or None
        self._driver = UiDriver()
        if sn:
            self._driver.connect(sn)
        else:
            self._driver.connect()
        self._driver.set_implicit_wait_time(Config.IMPLICIT_WAIT)
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
