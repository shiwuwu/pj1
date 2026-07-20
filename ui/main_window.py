"""主界面 —— 使用 customtkinter 现代化 UI 库。"""

import os
import re
import queue
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import customtkinter as ctk

from ui.test_runner import TestRunner, discover_features

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_MONO_FONT = ("Consolas", 10)


class MainWindow:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("HarmonyOS UI Test Runner")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)

        self._runner = TestRunner()
        self._poll_id: str = ""
        self._features_data: list[dict] = []
        self._last_report_path: str = ""
        self._bold_font = ctk.CTkFont(weight="bold", size=13)
        self._scenario_map: dict[str, list[str]] = {}
        self._feature_results: dict[str, dict[str, bool]] = {}

        self._build_ui()
        self._refresh_features()
        self._poll_queue()

    # --------------------------------------------------
    # 构建界面
    # --------------------------------------------------

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

        # --- 左侧控制面板 ---
        left = ctk.CTkFrame(self.root)
        left.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=0)
        left.grid_rowconfigure(1, weight=1)
        left.grid_rowconfigure(2, weight=0)
        left.grid_rowconfigure(3, weight=0)

        self._build_device_section(left)
        self._build_feature_tree(left)
        self._build_control_bar(left)
        self._build_progress(left)

        # --- 右侧输出面板 ---
        right = ctk.CTkFrame(self.root)
        right.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)
        self._build_output_area(right)

        # --- 底部状态栏 ---
        self._build_status_bar()

    def _build_device_section(self, parent: ctk.CTkFrame):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(frame, text="设备连接", font=self._bold_font).pack(
            anchor="w", padx=10, pady=(6, 4)
        )

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=(0, 6))
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inner, text="设备 SN:").grid(row=0, column=0, sticky="w")
        self._sn_var = tk.StringVar()
        sn_entry = ctk.CTkEntry(inner, textvariable=self._sn_var, width=180)
        sn_entry.grid(row=0, column=1, padx=(6, 6), sticky="ew")

        self._connect_btn = ctk.CTkButton(inner, text="连接", width=60, command=self._on_connect)
        self._connect_btn.grid(row=0, column=2)

        self._device_status_var = tk.StringVar(value="未连接")
        ctk.CTkLabel(inner, textvariable=self._device_status_var, text_color="gray").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

    def _build_feature_tree(self, parent: ctk.CTkFrame):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, pady=(0, 6))

        ctk.CTkLabel(frame, text="测试用例", font=self._bold_font).pack(
            anchor="w", padx=10, pady=(6, 4)
        )

        tree_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("status",),
            show="tree headings",
            selectmode="extended",
            height=14,
        )
        self._tree.heading("#0", text="Feature")
        self._tree.heading("status", text="")
        self._tree.column("#0", width=300)
        self._tree.column("status", width=50, anchor=tk.CENTER)
        self._tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._tree.tag_configure("feature", font=("", 10))
        self._tree.tag_configure("pass", foreground="#2a2")
        self._tree.tag_configure("fail", foreground="#d22")
        self._tree.tag_configure("running", foreground="#28f")

    def _build_control_bar(self, parent: ctk.CTkFrame):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 6))

        self._run_all_btn = ctk.CTkButton(frame, text="运行全部", width=90, command=self._on_run_all)
        self._run_all_btn.pack(side="left", padx=(0, 4))

        self._run_sel_btn = ctk.CTkButton(frame, text="运行选中", width=90, command=self._on_run_selected)
        self._run_sel_btn.pack(side="left", padx=(0, 4))

        self._stop_btn = ctk.CTkButton(frame, text="停止", width=60, command=self._on_stop, state="disabled")
        self._stop_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(frame, text="刷新", width=60, command=self._refresh_features).pack(side="left")

        default_lang = os.environ.get("TEST_LANG", "zh_CN")
        ctk.CTkLabel(frame, text="  语言:").pack(side="left")
        self._lang_var = tk.StringVar(value=default_lang)
        lang_menu = ctk.CTkOptionMenu(
            frame,
            values=["zh_CN", "zh_TW", "en", "all"],
            variable=self._lang_var,
            width=80,
            command=lambda _: self._refresh_features(),
        )
        lang_menu.pack(side="left", padx=(4, 0))

        self._report_btn = ctk.CTkButton(
            frame, text="查看报告", width=90, command=self._on_view_report, state="disabled"
        )
        self._report_btn.pack(side="right", padx=(4, 0))

    def _build_progress(self, parent: ctk.CTkFrame):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x")
        frame.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(frame, mode="determinate")
        self._progress.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._progress.set(0)

        self._progress_text = tk.StringVar(value="就绪")
        ctk.CTkLabel(frame, textvariable=self._progress_text, width=60).grid(row=0, column=1)

    def _build_output_area(self, parent: ctk.CTkFrame):
        ctk.CTkLabel(parent, text="输出日志", font=self._bold_font).pack(
            anchor="w", padx=10, pady=(6, 4)
        )

        self._output = ctk.CTkTextbox(parent, wrap="word", font=_MONO_FONT)
        self._output.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._output.tag_config("error", foreground="#d22")
        self._output.tag_config("pass", foreground="#2a2")
        self._output.tag_config("info", foreground="#28f")

    def _build_status_bar(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))

        self._status_var = tk.StringVar(value="就绪。请选择测试用例并点击运行。")
        ctk.CTkLabel(frame, textvariable=self._status_var).pack(side="left")

        self._stats_var = tk.StringVar(value="")
        ctk.CTkLabel(frame, textvariable=self._stats_var).pack(side="right")

    # --------------------------------------------------
    # 功能方法
    # --------------------------------------------------

    def _refresh_features(self):
        self._tree.delete(*self._tree.get_children())
        self._scenario_map.clear()
        lang_filter = self._lang_var.get()
        self._features_data = discover_features(lang_filter)
        lang_labels = {"zh_CN": "简中", "zh_TW": "繁中", "en": "EN"}

        for feat in self._features_data:
            lang = lang_labels.get(feat.get("lang", ""), feat.get("lang", ""))
            sc_count = len(feat["scenarios"])
            fid = self._tree.insert(
                "", tk.END,
                text=f"  [{lang}] {feat['name']}  ({sc_count} 个场景)",
                values=("○",), tags=("feature",),
            )
            for sc in feat["scenarios"]:
                self._scenario_map.setdefault(sc["name"], []).append(fid)

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
            self._connect_btn.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("连接失败", str(e))

    def _get_selected_scenarios(self) -> list[str]:
        """返回选中 Feature 下的所有场景名列表。"""
        names = []
        selected = set(self._tree.selection())
        for feat in self._features_data:
            match = any(
                fid in selected
                for sc in feat["scenarios"]
                for fid in self._scenario_map.get(sc["name"], [])
            )
            if match:
                for sc in feat["scenarios"]:
                    names.append(sc["name"])
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
        self._report_btn.configure(state="disabled")
        lang = self._lang_var.get()
        os.environ["TEST_LANG"] = lang
        self._runner = TestRunner()
        if features:
            self._runner.set_features(features)
        self._runner.start()

        self._run_all_btn.configure(state="disabled")
        self._run_sel_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
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
        if self._last_report_path and Path(self._last_report_path).exists():
            webbrowser.open(f"file:///{Path(self._last_report_path).resolve().as_posix()}")
        else:
            messagebox.showinfo("提示", "暂无测试报告，请先运行测试。")

    def _on_run_finished(self):
        self._run_all_btn.configure(state="normal")
        self._run_sel_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress_text.set("完成")
        if self._last_report_path:
            self._report_btn.configure(state="normal")

    def _clear_output(self):
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")

    def _clear_tree_status(self):
        self._feature_results.clear()
        for item in self._tree.get_children():
            self._tree.item(item, values=("○",), tags=("feature",))

    def _append_output(self, line: str):
        self._output.configure(state="normal")
        if "PASSED" in line or "passed" in line.lower():
            self._output.insert("end", line + "\n", "pass")
        elif "FAILED" in line or "FAILURES" in line or "error" in line.lower() or "错误" in line:
            self._output.insert("end", line + "\n", "error")
        elif "===" in line or "collected" in line or "test session" in line.lower():
            self._output.insert("end", line + "\n", "info")
        else:
            self._output.insert("end", line + "\n")
        self._output.see("end")
        self._output.configure(state="disabled")

    def _update_tree_result(self, scenario_name: str, passed: bool):
        for fid in self._scenario_map.get(scenario_name, []):
            if not self._tree.exists(fid):
                continue
            if fid not in self._feature_results:
                self._feature_results[fid] = {}
            self._feature_results[fid][scenario_name] = passed

            all_pass = all(self._feature_results[fid].values())
            if all_pass:
                self._tree.item(fid, values=("✓",), tags=("pass",))
            else:
                self._tree.item(fid, values=("✗",), tags=("fail",))

    # --------------------------------------------------
    # 消息轮询（从后台线程读取输出和结果）
    # --------------------------------------------------

    def _poll_queue(self):
        try:
            while True:
                msg_type, payload = self._runner.output_queue.get_nowait()
                if msg_type == "output":
                    self._append_output(payload)
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
                        self._report_btn.configure(state="normal")
        except queue.Empty:
            pass
        except Exception:
            pass

        self._poll_id = self.root.after(200, self._poll_queue)

    def _parse_summary(self):
        text = self._output.get("1.0", "end")
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
        self._progress.set(1.0)
        self._progress_text.set("完成")

    def on_close(self):
        if self._runner.is_running():
            self._runner.stop()
        if self._poll_id:
            self.root.after_cancel(self._poll_id)
        self.root.destroy()
