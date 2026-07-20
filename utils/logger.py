"""日志工具 —— 控制台输出，运行测试时同步写入 reports/ 目录。"""

import logging
import os
import sys
from pathlib import Path

_loggers: dict[str, logging.Logger] = {}
_file_handler: logging.FileHandler | None = None
_root: logging.Logger | None = None
_auto_file_checked = False


def _init_root():
    global _root
    if _root is not None:
        return
    _root = logging.getLogger("harmony_test")
    _root.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(fmt)
    _root.addHandler(console)


def get_logger(name: str = "harmony_test") -> logging.Logger:
    global _auto_file_checked
    _init_root()
    if not _auto_file_checked:
        _auto_file_checked = True
        log_file = os.environ.get("HARMONY_LOG_FILE", "")
        if log_file:
            enable_file_log(log_file)
    if name not in _loggers:
        if name == "harmony_test":
            _loggers[name] = logging.getLogger("harmony_test")
        else:
            _loggers[name] = logging.getLogger(f"harmony_test.{name}")
    return _loggers[name]


def enable_file_log(filepath: str):
    """开始将日志写入指定文件（用于测试运行时）。"""
    global _file_handler, _root
    _init_root()
    if _file_handler is not None:
        return
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    _file_handler = logging.FileHandler(filepath, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_root.handlers[0].formatter)
    _root.addHandler(_file_handler)


def disable_file_log():
    """停止日志写入文件。"""
    global _file_handler, _root
    if _file_handler is None or _root is None:
        return
    _root.removeHandler(_file_handler)
    _file_handler.close()
    _file_handler = None
