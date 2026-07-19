"""HarmonyOS UI Test Runner —— 可视化测试管理界面

启动方式:
    python run_ui.py

依赖:
    - Tkinter（Python 内置，Win/Mac 无需安装）
    - hypium, pytest-bdd（已在 requirements 中）
"""

import sys
import tkinter as tk
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import MainWindow


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
