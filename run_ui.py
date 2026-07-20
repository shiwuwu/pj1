"""HarmonyOS UI Test Runner —— 可视化测试管理界面

启动方式:
    python run_ui.py

依赖:
    - customtkinter
    - hypium, pytest-bdd
"""

import sys
import customtkinter as ctk
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
