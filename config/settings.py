"""工具配置 —— 日志抓取、输出路径等默认设置。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class LogSettings:
    # 日志输出目录
    log_dir: str = field(
        default_factory=lambda: os.environ.get(
            "HARMONY_LOG_DIR", str(PROJECT_ROOT / "logs")
        )
    )
    # hdc 可执行文件路径
    hdc_path: str = field(
        default_factory=lambda: os.environ.get("HDC_PATH", "hdc")
    )
    # 默认设备 SN
    device_sn: str = field(
        default_factory=lambda: os.environ.get("HARMONY_DEVICE_SN", "")
    )
    # 默认日志级别过滤 (D/I/W/E/F)
    log_level: str = "I"
    # 抓取默认时长（秒），0 表示持续
    default_duration: int = 0
    # 日志文件编码
    encoding: str = "utf-8"
    # 日志文件名时间戳格式
    ts_format: str = "%Y%m%d_%H%M%S"


settings = LogSettings()
