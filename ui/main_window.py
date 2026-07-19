"""主界面 —— 使用 Tkinter (Win/Mac 内置，零额外依赖)。"""

import re
import queue
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ui.test_runner import TestRunner, discover_features

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# 主窗口
# ============================================================

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("HarmonyOS UI Test Runner")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)

        self._runner = TestRunner()
        self._poll_id: str = ""
        self._features_data: list[dict] = []
        self._last_report_path: str = ""   # 最近一次生成的报告路径

        self._build_ui()
        self._refresh_features()
        self._poll_queue()

    # --------------------------------------------------
    # 构建界面
    # --------------------------------------------------

    def _build_ui(self):
        # 主分隔面板
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # --- 左侧控制面板 ---
        left = ttk.Frame(paned, width=380)
        paned.add(left, weight=0)

        self._build_device_section(left)
        self._build_feature_tree(left)
        self._build_control_bar(left)
        self._build_progress(left)

        # --- 右侧输出面板 ---
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        self._build_output_area(right)

        # --- 底部状态栏 ---
        self._build_status_bar()

    def _build_device_section(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="设备连接", padding=6)
        frame.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(frame, text="设备 SN:").grid(row=0, column=0, sticky=tk.W)
        self._sn_var = tk.StringVar()
        sn_entry = ttk.Entry(frame, textvariable=self._sn_var, width=22)
        sn_entry.grid(row=0, column=1, padx=(6, 6), sticky=tk.EW)

        self._connect_btn = ttk.Button(frame, text="连接", command=self._on_connect)
        self._connect_btn.grid(row=0, column=2)

        self._device_status_var = tk.StringVar(value="未连接")
        ttk.Label(frame, textvariable=self._device_status_var, foreground="gray").grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=(4, 0)
        )
        frame.columnconfigure(1, weight=1)

    def _build_feature_tree(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="测试用例", padding=6)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Treeview: checkbox → feature → scenario
        self._tree = ttk.Treeview(
            frame,
            columns=("status",),
            show="tree headings",
            selectmode="extended",
            height=14,
        )
        self._tree.heading("#0", text="Feature / Scenario")
        self._tree.heading("status", text="")
        self._tree.column("#0", width=260)
        self._tree.column("status", width=60, anchor=tk.CENTER)
        self._tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self._tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.tag_configure("feature", font=("", 10, "bold"))
        self._tree.tag_configure("scenario", font=("", 9))
        self._tree.tag_configure("pass", foreground="#2a2")
        self._tree.tag_configure("fail", foreground="#d22")
        self._tree.tag_configure("running", foreground="#28f")

    def _build_control_bar(self, parent: ttk.Frame):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 6))

        self._run_all_btn = ttk.Button(frame, text="▶ 运行全部", command=self._on_run_all)
        self._run_all_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._run_sel_btn = ttk.Button(frame, text="▶ 运行选中", command=self._on_run_selected)
        self._run_sel_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._stop_btn = ttk.Button(frame, text="■ 停止", command=self._on_stop, state=tk.DISABLED)
        self._stop_btn.pack(side=tk.LEFT, padx=(0, 4))

        ttk.Button(frame, text="↻ 刷新", command=self._refresh_features).pack(side=tk.LEFT)

        ttk.Label(frame, text="  语言:").pack(side=tk.LEFT)
        self._lang_var = tk.StringVar(value="all")
        lang_combo = ttk.Combobox(
            frame, textvariable=self._lang_var, values=["all", "zh_CN", "zh_TW", "en"],
            state="readonly", width=6,
        )
        lang_combo.pack(side=tk.LEFT, padx=(4, 0))
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_features())

        self._report_btn = ttk.Button(
            frame, text="📊 查看报告", command=self._on_view_report, state=tk.DISABLED
        )
        self._report_btn.pack(side=tk.RIGHT, padx=(4, 0))

    def _build_progress(self, parent: ttk.Frame):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X)

        self._progress = ttk.Progressbar(frame, mode="determinate")
        self._progress.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self._progress_text = tk.StringVar(value="就绪")
        ttk.Label(frame, textvariable=self._progress_text, width=10).pack(side=tk.RIGHT, padx=(6, 0))

    def _build_output_area(self, parent: ttk.Frame):
        frame = ttk.LabelFrame(parent, text="输出日志", padding=4)
        frame.pack(fill=tk.BOTH, expand=True)

        self._output = tk.Text(frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", "Menlo", "Monaco", "monospace", 10))
        self._output.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self._output, orient=tk.VERTICAL, command=self._output.yview)
        self._output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 颜色标签
        self._output.tag_configure("error", foreground="#d22")
        self._output.tag_configure("pass", foreground="#2a2")
        self._output.tag_configure("info", foreground="#28f")
        self._output.tag_configure("bold", font=("Consolas", "Menlo", "Monaco", "monospace", 10, "bold"))

    def _build_status_bar(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.X, side=tk.BOTTOM, padx=6, pady=(0, 6))

        self._status_var = tk.StringVar(value="就绪。请选择测试用例并点击运行。")
        ttk.Label(frame, textvariable=self._status_var).pack(side=tk.LEFT)

        self._stats_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self._stats_var).pack(side=tk.RIGHT)

    # --------------------------------------------------
    # 功能方法
    # --------------------------------------------------

    def _refresh_features(self):
        """重新扫描 features 目录并刷新树形列表（含语言标签）。"""
        self._tree.delete(*self._tree.get_children())
        lang_filter = self._lang_var.get()
        self._features_data = discover_features(lang_filter)
        lang_labels = {"zh_CN": "简中", "zh_TW": "繁中", "en": "EN"}

        for feat in self._features_data:
            lang = lang_labels.get(feat.get("lang", ""), feat.get("lang", ""))
            fid = self._tree.insert(
                "", tk.END,
                text=f"  [{lang}] {feat['name']}",
                values=("",), tags=("feature",), open=True,
            )
            for sc in feat["scenarios"]:
                self._tree.insert(
                    fid, tk.END, text=f"  {sc['name']}", values=("○",), tags=("scenario",)
                )

        count = len(self._features_data)
        self._status_var.set(f"已加载 {count} 个 Feature 文件（简中/繁中/EN）。")

    def _on_connect(self):
        sn = self._sn_var.get().strip()
        if not sn:
            messagebox.showwarning("提示", "请输入设备 SN")
            return
        try:
            from hypium import UiDriver
            driver = UiDriver()
            driver.connect(sn)
            self._device_status_var.set(f"已连接: {sn}")
            self._connect_btn.configure(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("连接失败", str(e))

    def _get_selected_scenarios(self) -> list[str]:
        """获取树中选中的场景名列表。"""
        names = []
        for item in self._tree.selection():
            text = self._tree.item(item, "text").strip()
            if text and self._tree.parent(item):  # 只取场景节点（有父节点 = feature）
                names.append(text)
        return names

    def _on_run_all(self):
        if self._runner.is_running():
            messagebox.showinfo("提示", "测试正在运行中，请等待完成。")
            return
        self._start_run(features=[])

    def _on_run_selected(self):
        if self._runner.is_running():
            messagebox.showinfo("提示", "测试正在运行中，请等待完成。")
            return
        selected = self._get_selected_scenarios()
        if not selected:
            messagebox.showinfo("提示", "请先在左侧树中选中要运行的场景。")
            return
        self._start_run(features=selected)

    def _start_run(self, features: list[str]):
        self._clear_output()
        self._clear_tree_status()
        self._last_report_path = ""
        self._report_btn.configure(state=tk.DISABLED)
        # 传递当前语言选择到子进程
        import os
        lang = self._lang_var.get()
        os.environ["TEST_LANG"] = lang
        self._runner = TestRunner()
        if features:
            self._runner.set_features(features)
        self._runner.start()

        self._run_all_btn.configure(state=tk.DISABLED)
        self._run_sel_btn.configure(state=tk.DISABLED)
        self._stop_btn.configure(state=tk.NORMAL)
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        self._progress_text.set("运行中...")
        self._status_var.set("测试运行中...")
        self._stats_var.set("")

    def _on_stop(self):
        if self._runner.is_running():
            self._runner.stop()
            self._on_run_finished()

    def _on_view_report(self):
        """在浏览器中打开最近一次测试报告。"""
        if self._last_report_path and Path(self._last_report_path).exists():
            webbrowser.open(f"file:///{Path(self._last_report_path).resolve().as_posix()}")
        else:
            messagebox.showinfo("提示", "暂无测试报告，请先运行测试。")

    def _on_run_finished(self):
        self._run_all_btn.configure(state=tk.NORMAL)
        self._run_sel_btn.configure(state=tk.NORMAL)
        self._stop_btn.configure(state=tk.DISABLED)
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress_text.set("完成")
        if self._last_report_path:
            self._report_btn.configure(state=tk.NORMAL)

    def _clear_output(self):
        self._output.configure(state=tk.NORMAL)
        self._output.delete("1.0", tk.END)
        self._output.configure(state=tk.DISABLED)

    def _clear_tree_status(self):
        for item in self._tree.get_children():
            self._tree.item(item, values=("",))
            for child in self._tree.get_children(item):
                self._tree.item(child, values=("○",), tags=("scenario",))

    def _append_output(self, line: str):
        self._output.configure(state=tk.NORMAL)
        if "PASSED" in line or "passed" in line.lower():
            self._output.insert(tk.END, line + "\n", "pass")
        elif "FAILED" in line or "FAILURES" in line or "error" in line.lower() or "错误" in line:
            self._output.insert(tk.END, line + "\n", "error")
        elif "===" in line or "collected" in line or "test session" in line.lower():
            self._output.insert(tk.END, line + "\n", "bold")
        else:
            self._output.insert(tk.END, line + "\n")
        self._output.see(tk.END)
        self._output.configure(state=tk.DISABLED)

    def _update_tree_result(self, scenario_name: str, passed: bool):
        for fid in self._tree.get_children():
            for sid in self._tree.get_children(fid):
                text = self._tree.item(sid, "text").strip()
                if text == scenario_name:
                    if passed:
                        self._tree.item(sid, values=("✓",), tags=("pass",))
                    else:
                        self._tree.item(sid, values=("✗",), tags=("fail",))
                    return

    # --------------------------------------------------
    # 消息轮询（从后台线程读取输出和结果）
    # --------------------------------------------------

    def _poll_queue(self):
        """定时从 runner 的输出队列中取消息并在主线程更新 UI。"""
        try:
            while True:
                msg_type, payload = self._runner.output_queue.get_nowait()
                if msg_type == "output":
                    self._append_output(payload)
                    # 尝试匹配 PASSED/FAILED 更新树
                    m = re.match(r"^\s*PASSED\s+.+::test_(.+?)\b", payload)
                    if m:
                        self._update_tree_result(m.group(1), passed=True)
                    m2 = re.match(r"^\s*FAILED\s+.+::test_(.+?)\b", payload)
                    if m2:
                        self._update_tree_result(m2.group(1), passed=False)
                elif msg_type == "result":
                    self._status_var.set(f"测试完成，退出码: {payload}")
                elif msg_type == "report":
                    self._last_report_path = payload
                    self._append_output(f"\n[报告] HTML 报告已生成: {payload}")
                elif msg_type == "done":
                    self._on_run_finished()
                    self._parse_summary()
                    if self._last_report_path:
                        self._report_btn.configure(state=tk.NORMAL)
        except queue.Empty:
            pass

        self._poll_id = self.root.after(200, self._poll_queue)

    def _parse_summary(self):
        """从输出日志中解析测试统计。"""
        text = self._output.get("1.0", tk.END)
        passed = int(m.group(1)) if (m := re.search(r"(\d+)\s+passed", text)) else 0
        failed = int(m.group(1)) if (m := re.search(r"(\d+)\s+failed", text)) else 0
        skipped = int(m.group(1)) if (m := re.search(r"(\d+)\s+skipped", text)) else 0
        errors = int(m.group(1)) if (m := re.search(r"(\d+)\s+errors?", text)) else 0
        total = passed + failed + skipped + errors
        parts = [f"共 {total} 个测试", f"通过 {passed}"]
        if failed:
            parts.append(f"失败 {failed}")
        if skipped:
            parts.append(f"跳过 {skipped}")
        self._stats_var.set(" | ".join(parts))
        self._progress["value"] = 100
        self._progress_text.set("完成")

    def on_close(self):
        if self._runner.is_running():
            self._runner.stop()
        if self._poll_id:
            self.root.after_cancel(self._poll_id)
        self.root.destroy()
