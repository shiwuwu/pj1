"""后台线程执行 pytest-bdd 测试，实时捕获输出，运行结束后生成 HTML 报告。"""

import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"


class TestRunner(threading.Thread):
    """在子进程中运行 pytest（带 --html），通过队列实时输出每一行。

    运行结束后自动生成：
    1. pytest-html 标准报告 → reports/pytest_report_<ts>.html
    2. 自定义 Summary 报告 → reports/test_report_<ts>.html
    """

    def __init__(self):
        super().__init__(daemon=True)
        self._process: subprocess.Popen | None = None
        self._queue = queue.Queue()
        self._running = False
        self._features: list[str] = []
        self._output_lines: list[str] = []
        self._start_time: float = 0
        self._pytest_html_path: str = ""
        self._custom_html_path: str = ""

    @property
    def output_queue(self) -> queue.Queue:
        return self._queue

    @property
    def pytest_html_path(self) -> str:
        return self._pytest_html_path

    @property
    def custom_html_path(self) -> str:
        return self._custom_html_path

    def set_features(self, features: list[str]):
        """设置要运行的 feature 文件列表，空列表 = 全部。"""
        self._features = features

    def run(self):
        self._running = True
        self._output_lines = []
        self._start_time = time.time()
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._pytest_html_path = str(REPORT_DIR / f"pytest_report_{ts}.html")

        args = [
            sys.executable, "-m", "pytest",
            str(PROJECT_ROOT / "testcases"),
            "-v",
            "--tb=short",
            "--color=no",
            f"--html={self._pytest_html_path}",
            "--self-contained-html",
        ]
        if self._features:
            k_expr = " or ".join(self._features)
            args.extend(["-k", k_expr])

        try:
            self._process = subprocess.Popen(
                args,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            for line in self._process.stdout:
                clean = line.rstrip("\r\n")
                self._output_lines.append(clean)
                self._queue.put(("output", clean))
            self._process.wait()
            rc = self._process.returncode
            self._queue.put(("result", rc))

            # 生成自定义 Summary 报告
            self._generate_custom_report()

            self._queue.put(("done", None))
        except Exception as e:
            self._queue.put(("output", f"\n[错误] {e}"))
            self._queue.put(("done", None))
        finally:
            self._running = False

    def _generate_custom_report(self):
        """调用 utils.report 生成自定义 HTML 报告。"""
        try:
            from utils.report import generate_summary_report
            full_output = "\n".join(self._output_lines)
            features_data = discover_features()
            duration = time.time() - self._start_time
            self._custom_html_path = generate_summary_report(
                full_output, features_data, duration
            )
            self._queue.put(("report", self._custom_html_path))
        except Exception as e:
            self._queue.put(("output", f"\n[报告生成失败] {e}"))

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            time.sleep(0.5)
            if self._process.poll() is None:
                self._process.kill()
            self._queue.put(("output", "\n[用户中止] 测试已被手动停止"))
            self._running = False

    def is_running(self) -> bool:
        return self._running


def discover_features(lang: str = "all") -> list[dict]:
    """扫描 features/.generated/{zh_CN,zh_TW,en} 目录，可按语言过滤。"""
    import os
    lang_filter = lang if lang != "all" else os.environ.get("TEST_LANG", "all")
    features_root = PROJECT_ROOT / "testcases" / "features"
    generated_root = features_root / ".generated"
    results = []

    scan_root = generated_root if generated_root.exists() else features_root

    for lang_dir in sorted(scan_root.iterdir()):
        if not lang_dir.is_dir():
            continue
        lang = lang_dir.name
        if lang_filter != "all" and lang != lang_filter:
            continue

        for fpath in sorted(lang_dir.glob("*.feature")):
            content = fpath.read_text(encoding="utf-8")

            # Feature 名称（支持中英文关键字）
            feature_name = fpath.stem
            fm = re.search(r"^(?:Feature|功能):\s*(.+)$", content, re.MULTILINE)
            if fm:
                feature_name = fm.group(1).strip()

            # 提取 Background 步骤
            bg_match = re.search(
                r"^\s*(?:Background|背景):\s*$(.+?)(?:^\s*@|\s*(?:Scenario|场景|場景):)",
                content, re.MULTILINE | re.DOTALL,
            )
            bg_steps = _extract_steps(bg_match.group(1)) if bg_match else []

            # 解析每个 Scenario（支持中英文关键字）
            scenarios = []
            blocks = re.split(r"^\s*(?:Scenario|场景|場景):\s*(.+)$", content, flags=re.MULTILINE)
            for i in range(1, len(blocks), 2):
                sc_name = blocks[i].strip()
                sc_body = blocks[i + 1] if i + 1 < len(blocks) else ""
                all_steps = bg_steps + _extract_steps(sc_body)
                scenarios.append({"name": sc_name, "steps": all_steps})

            results.append({
                "path": str(fpath.relative_to(PROJECT_ROOT)),
                "name": feature_name,
                "lang": lang,
                "scenarios": scenarios,
            })

    return results


def _extract_steps(body: str) -> list[str]:
    """从 Scenario body 提取 Given/When/Then/And/But 等步骤行，支持中英文关键字。"""
    steps = []
    _kw = r"(?:Given|When|Then|And|But|假如|假設|假定|假设|當|当|那麼|那么|而且|並且|并且|同時|同时|但是)"
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("@"):
            continue
        if re.match(rf"^{_kw}\s", stripped):
            steps.append(stripped)
    return steps
