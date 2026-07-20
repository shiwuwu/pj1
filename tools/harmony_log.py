"""鸿蒙设备日志抓取工具 —— 通过 hdc hilog 抓取并输出设备日志。"""

import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from config.settings import settings
from utils.logger import get_logger
from tools.hdc_utils import HdcHelper

_log = get_logger("tools.harmony_log")


class HarmonyLogCapture:
    """鸿蒙日志抓取器，封装 hdc hilog 命令。

    用法::

        cap = HarmonyLogCapture(device_sn="xxx")
        cap.clear()
        output = cap.collect(duration=10, level="I")
        cap.save_to_file("crash.log", duration=5, level="E")
        cap.stream(callback=lambda line: print(line))
    """

    def __init__(self, device_sn: str = ""):
        self.device_sn = device_sn or settings.device_sn
        self.log_dir = Path(settings.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._hdc = HdcHelper(self.device_sn)
        self._process: Optional[subprocess.Popen] = None
        self._streaming = False

    # --------------------------------------------------
    # 核心操作
    # --------------------------------------------------

    def clear(self) -> bool:
        """清除设备日志缓冲区。"""
        try:
            self._hdc.shell("hilog -c")
            return True
        except Exception as e:
            _log.error(f"清空日志失败: {e}")
            return False

    def collect(
        self,
        duration: int = 0,
        level: str = "",
        tag: str = "",
        domain: str = "",
        output_file: str = "",
    ) -> str:
        """抓取日志并返回字符串。

        参数:
            duration: 抓取时长（秒），0 = 仅读取当前已有日志
            level: 过滤级别 D/I/W/E/F
            tag: 过滤标签
            domain: 过滤 domain
            output_file: 同时保存到的文件路径（可选）
        """
        level = level or settings.log_level
        duration = duration or settings.default_duration

        if duration > 0:
            return self._collect_timed(duration, level, tag, domain, output_file)
        return self._collect_once(level, tag, domain, output_file)

    def _collect_once(self, level: str, tag: str, domain: str, output_file: str) -> str:
        """一次性读取当前日志缓冲区。"""
        args = ["hilog"]
        if level:
            args.extend(["-l", level])
        if tag:
            args.extend(["-t", tag])
        if domain:
            args.extend(["-D", domain])
        try:
            result = self._hdc.shell(" ".join(args), timeout=30)
            output = result.stdout
            if output_file:
                self._write_file(output_file, output)
            return output
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            return f"[HarmonyLogCapture] 抓取失败: {e}"

    def _collect_timed(self, duration: int, level: str, tag: str,
                       domain: str, output_file: str) -> str:
        """按指定时长抓取日志：先清空缓冲区，等待后读取。"""
        self.clear()
        time.sleep(duration)
        return self._collect_once(level, tag, domain, output_file)

    def save_to_file(
        self, filename: str = "", duration: int = 0,
        level: str = "", tag: str = "", domain: str = "",
    ) -> str:
        """抓取日志并保存到文件。返回文件完整路径。"""
        if not filename:
            ts = datetime.now().strftime(settings.ts_format)
            filename = f"harmony_log_{ts}.log"
        filepath = str(
            Path(filename) if Path(filename).is_absolute() else self.log_dir / filename
        )
        self.collect(duration=duration, level=level, tag=tag,
                     domain=domain, output_file=filepath)
        _log.info(f"日志已保存: {filepath}")
        return filepath

    # --------------------------------------------------
    # 实时流
    # --------------------------------------------------

    def stream(
        self, callback: Callable[[str], None],
        level: str = "", tag: str = "", domain: str = "",
    ):
        """在后台线程中实时抓取日志，每行通过 callback 输出。

        用法::

            cap.stream(lambda line: print(line), level="E")
            time.sleep(30)
            cap.stop()
        """
        args = ["hilog", "-r"]
        if level:
            args.extend(["-l", level])
        if tag:
            args.extend(["-t", tag])
        if domain:
            args.extend(["-D", domain])

        cmd = self._hdc._cmd("shell") + args
        self._streaming = True

        def _run():
            try:
                self._process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding=settings.encoding,
                )
                for line in self._process.stdout:
                    if not self._streaming:
                        self._process.terminate()
                        break
                    callback(line.rstrip("\r\n"))
            except Exception as e:
                callback(f"[HarmonyLogCapture] 实时日志异常: {e}")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """停止实时日志抓取。"""
        self._streaming = False
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

    # --------------------------------------------------
    # 辅助
    # --------------------------------------------------

    def _write_file(self, filepath: str, content: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        Path(filepath).write_text(content, encoding=settings.encoding)

    def get_last_logs(self, count: int = 50, level: str = "") -> str:
        """获取最近 N 条日志。"""
        output = self.collect(duration=0, level=level)
        lines = [l for l in output.split("\n") if l.strip()]
        return "\n".join(lines[-count:])
