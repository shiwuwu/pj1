"""HDC 工具类 —— 封装 HarmonyOS Device Connector 常用命令。"""

import subprocess
from pathlib import Path
from typing import Optional

from config.settings import settings
from utils.logger import get_logger

_log = get_logger("tools.hdc")


class HdcHelper:
    """HDC 命令封装，自动处理设备选择和错误捕获。

    用法::

        hdc = HdcHelper(device_sn="xxx")
        devices = hdc.list_devices()
        hdc.push("local.txt", "/data/local/tmp/remote.txt")
        result = hdc.shell("ls /data/local/tmp")
    """

    def __init__(self, device_sn: str = ""):
        self.device_sn = device_sn or settings.device_sn

    # --------------------------------------------------
    # 内部
    # --------------------------------------------------

    def _cmd(self, *args: str) -> list[str]:
        cmd = [settings.hdc_path]
        if self.device_sn:
            cmd += ["-t", self.device_sn]
        cmd += list(args)
        return cmd

    def _run(self, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """执行 hdc 命令，返回 CompletedProcess。"""
        cmd = self._cmd(*args)
        _log.debug(f"hdc: {' '.join(cmd)}")
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            _log.error(f"hdc 未找到，请确认 {settings.hdc_path} 已安装并在 PATH 中")
            return subprocess.CompletedProcess(cmd, -1, stdout="", stderr="hdc not found")
        except subprocess.TimeoutExpired:
            _log.error(f"hdc 命令超时: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, -1, stdout="", stderr="timeout")

    # --------------------------------------------------
    # 设备管理
    # --------------------------------------------------

    def list_devices(self) -> list[dict]:
        """列出已连接设备。返回 [{"sn": str, "status": str}, ...]。

        状态: "device"=正常, "unauthorized"=未授权, "offline"=离线
        """
        result = self._run("list", "targets")
        devices = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                devices.append({"sn": parts[0], "status": parts[1]})
        return devices

    def first_device(self) -> Optional[str]:
        """获取第一台在线设备的 SN，没有则返回 None。"""
        for d in self.list_devices():
            if d["status"] == "device":
                return d["sn"]
        return None

    def is_connected(self) -> bool:
        """设备是否已连接且在线。"""
        if not self.device_sn:
            return False
        for d in self.list_devices():
            if d["sn"] == self.device_sn and d["status"] == "device":
                return True
        return False

    # --------------------------------------------------
    # Shell 命令
    # --------------------------------------------------

    def shell(self, command: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """在设备上执行 shell 命令。"""
        return self._run("shell", command, timeout=timeout)

    def shell_output(self, command: str, timeout: int = 30) -> str:
        """执行 shell 命令并返回 stdout 字符串。"""
        return self.shell(command, timeout=timeout).stdout.strip()

    # --------------------------------------------------
    # 应用管理
    # --------------------------------------------------

    def install(self, hap_path: str, replace: bool = True) -> bool:
        """安装 HAP 应用包。

        参数:
            hap_path: HAP 文件路径
            replace: 是否替换已有应用（-r）
        返回:
            是否安装成功
        """
        args = ["install"]
        if replace:
            args.append("-r")
        args.append(hap_path)
        result = self._run(*args)
        if result.returncode == 0:
            _log.info(f"应用安装成功: {hap_path}")
            return True
        _log.error(f"应用安装失败: {result.stderr.strip()}")
        return False

    def uninstall(self, package: str) -> bool:
        """卸载应用。"""
        result = self._run("uninstall", package)
        if result.returncode == 0:
            _log.info(f"应用卸载成功: {package}")
            return True
        _log.error(f"应用卸载失败: {result.stderr.strip()}")
        return False

    def start_app(self, ability: str) -> bool:
        """启动 Ability。

        参数:
            ability: 格式 "bundle_name/.AbilityName" 或 "bundle_name"
        """
        return self._run("shell", "aa", "start", "-a", "EntryAbility", "-b", ability)

    def stop_app(self, package: str) -> bool:
        """停止应用。"""
        result = self._run("shell", "aa", "force-stop", package)
        return result.returncode == 0

    # --------------------------------------------------
    # 文件传输
    # --------------------------------------------------

    def push(self, local: str, remote: str) -> bool:
        """推送文件到设备。

        用法::

            hdc.push("config.json", "/data/local/tmp/config.json")
        """
        result = self._run("file", "send", local, remote)
        if result.returncode == 0:
            _log.info(f"文件已推送: {local} → {remote}")
            return True
        _log.error(f"推送失败: {result.stderr.strip()}")
        return False

    def pull(self, remote: str, local: str) -> bool:
        """从设备拉取文件。

        用法::

            hdc.pull("/data/local/tmp/log.txt", "./logs/device_log.txt")
        """
        Path(local).parent.mkdir(parents=True, exist_ok=True)
        result = self._run("file", "recv", remote, local)
        if result.returncode == 0:
            _log.info(f"文件已拉取: {remote} → {local}")
            return True
        _log.error(f"拉取失败: {result.stderr.strip()}")
        return False

    # --------------------------------------------------
    # 设备信息
    # --------------------------------------------------

    def get_prop(self, prop: str) -> str:
        """获取设备属性。

        用法::

            hdc.get_prop("ro.build.version.release")
            hdc.get_prop("hw_sc.build.platform.version")
        """
        return self.shell_output(f"getprop {prop}")

    def get_screen_size(self) -> str:
        """获取屏幕分辨率，如 "1080x2340"。"""
        output = self.shell_output("wm size")
        # 输出格式: "Physical size: 1080x2340"
        return output.split(":")[-1].strip() if ":" in output else output

    def get_android_version(self) -> str:
        """获取系统版本。"""
        return self.get_prop("ro.build.version.release")

    def get_device_model(self) -> str:
        """获取设备型号。"""
        return self.get_prop("ro.product.model")

    def list_packages(self, filter_text: str = "") -> list[str]:
        """列出已安装的应用包名，可按关键字过滤。"""
        output = self.shell_output("bm dump -a")
        packages = []
        for line in output.split("\n"):
            line = line.strip()
            if line and (not filter_text or filter_text in line):
                packages.append(line)
        return packages

    # --------------------------------------------------
    # 按键操作
    # --------------------------------------------------

    def press_key(self, key_code: int) -> bool:
        """发送按键事件。"""
        result = self._run("shell", "uitest", "uiInput", "keyEvent", str(key_code))
        return result.returncode == 0

    def press_home(self) -> bool:
        """按 Home 键 (keyCode=3)。"""
        _log.info("按键: Home")
        return self.press_key(3)

    def press_back(self) -> bool:
        """按返回键 (keyCode=4)。"""
        _log.info("按键: Back")
        return self.press_key(4)

    def press_power(self) -> bool:
        """按电源键 (keyCode=26)。"""
        _log.info("按键: Power")
        return self.press_key(26)

    def press_volume_up(self) -> bool:
        """按音量+ (keyCode=24)。"""
        _log.info("按键: Volume Up")
        return self.press_key(24)

    def press_volume_down(self) -> bool:
        """按音量- (keyCode=25)。"""
        _log.info("按键: Volume Down")
        return self.press_key(25)

    def press_enter(self) -> bool:
        """按回车键 (keyCode=66)。"""
        _log.info("按键: Enter")
        return self.press_key(66)

    def press_menu(self) -> bool:
        """按菜单键 (keyCode=82)。"""
        _log.info("按键: Menu")
        return self.press_key(82)

    def press_recent(self) -> bool:
        """按最近任务键 (keyCode=187)。"""
        _log.info("按键: Recent")
        return self.press_key(187)

    def press_camera(self) -> bool:
        """按相机键 (keyCode=27)。"""
        _log.info("按键: Camera")
        return self.press_key(27)

    def press_search_key(self) -> bool:
        """按搜索键 (keyCode=84)。"""
        _log.info("按键: Search")
        return self.press_key(84)

    def press_dpad_up(self) -> bool:
        """按方向键 ↑ (keyCode=19)。"""
        return self.press_key(19)

    def press_dpad_down(self) -> bool:
        """按方向键 ↓ (keyCode=20)。"""
        return self.press_key(20)

    def press_dpad_left(self) -> bool:
        """按方向键 ← (keyCode=21)。"""
        return self.press_key(21)

    def press_dpad_right(self) -> bool:
        """按方向键 → (keyCode=22)。"""
        return self.press_key(22)

    def press_dpad_center(self) -> bool:
        """按方向键中心确认 (keyCode=23)。"""
        return self.press_key(23)

    def long_press_key(self, key_code: int, duration_ms: int = 1000) -> bool:
        """长按某个按键（默认 1 秒）。"""
        _log.info(f"长按: keyCode={key_code} ({duration_ms}ms)")
        return self.press_key(key_code)  # HarmonyOS uitest 暂不支持直接长按

    # --------------------------------------------------
    # 系统操作
    # --------------------------------------------------

    def reboot(self) -> bool:
        """重启设备。"""
        result = self._run("target", "boot")
        return result.returncode == 0

    def screenshot(self, remote_path: str = "/data/local/tmp/screenshot.png",
                   local_path: str = "") -> Optional[str]:
        """截取设备屏幕并拉取到本地。

        参数:
            remote_path: 设备端临时截图路径
            local_path: 本地保存路径，为空则自动生成
        返回:
            本地文件路径，失败返回 None
        """
        if not local_path:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = f"screenshot_{ts}.png"

        self.shell(f"snapshot_display -f {remote_path}")
        if self.pull(remote_path, local_path):
            self.shell(f"rm {remote_path}")
            _log.info(f"截图已保存: {local_path}")
            return local_path
        return None
