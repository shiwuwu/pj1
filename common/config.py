"""全局配置常量，通过环境变量覆盖默认值。"""

import os


class Config:
    # 目标设备 SN，为空则自动选择
    DEVICE_SN = os.environ.get("HARMONY_DEVICE_SN", "")

    # 隐式等待超时（秒）
    IMPLICIT_WAIT = int(os.environ.get("HARMONY_IMPLICIT_WAIT", "10"))

    # 操作间隔（秒）
    ACTION_INTERVAL = float(os.environ.get("HARMONY_ACTION_INTERVAL", "1.0"))

    # 截图保存目录
    SCREENSHOT_DIR = os.environ.get(
        "HARMONY_SCREENSHOT_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots"),
    )
