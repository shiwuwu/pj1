"""conftest.py —— 连接 common/utils 层，为所有步骤定义提供 fixture。

架构关系:
    testcases/steps/test_*.py   ← 步骤定义（只写 Given/When/Then）
        ↓ 依赖 fixture
    testcases/steps/conftest.py ← fixture 工厂
        ↓ 调用
    common/                     ← DriverManager + Config
    utils/                      ← ScreenshotHelper, ComponentHelper, device_utils
        ↓ 底层
    hypium.UiDriver             ← 与 HarmonyOS 设备通信
"""

import os
import pytest

from common import DriverManager, Config
from utils import ScreenshotHelper, ComponentHelper, get_logger

logger = get_logger(__name__)


# ============================================================
# 语言选择 —— 控制运行哪种语言的 feature 文件
# ============================================================

LANG_LABELS = {"zh_CN": "简体中文", "zh_TW": "繁體中文", "en": "English"}


def get_active_langs(config=None) -> list[str]:
    """返回当前应运行的语言列表（优先读取 TEST_LANG 环境变量）。"""
    lang = os.environ.get("TEST_LANG", "all")
    if lang == "all":
        return list(LANG_LABELS.keys())
    return [lang]


@pytest.fixture(scope="session")
def driver_manager():
    """Driver 管理器 —— 会话级，整个测试过程共享一个连接。"""
    mgr = DriverManager()
    mgr.connect()
    yield mgr
    mgr.close()


@pytest.fixture
def driver(driver_manager: DriverManager):
    """每个测试用例注入的 UiDriver 实例。"""
    return driver_manager.driver


@pytest.fixture
def comp(driver):
    """组件操作辅助类。"""
    return ComponentHelper(driver)


@pytest.fixture
def screenshot(driver):
    """截图辅助类。"""
    return ScreenshotHelper(driver)


@pytest.fixture(scope="session")
def screenshot_dir():
    """确保截图根目录存在。"""
    import os
    os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
    return Config.SCREENSHOT_DIR


# ============================================================
# pytest-bdd 钩子
# ============================================================

def pytest_bdd_apply_tag(tag, function):
    """支持 @skip 标签跳过场景。"""
    if tag == "skip":
        marker = pytest.mark.skip(reason="Tagged with @skip")
        marker(function)
        return True
    return False


def pytest_bdd_step_error(exception, **kwargs):
    """步骤失败时自动截图。"""
    logger.error(f"步骤失败: {exception}")
    # 不在此处截图以避免循环依赖，由 fixture teardown 处理


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        try:
            dm = item.funcargs.get("driver_manager")
            if dm:
                helper = ScreenshotHelper(dm.driver)
                helper.take_on_fail(item.name)
        except Exception as exc:
            logger.warning(f"失败截图未能保存: {exc}")


# ============================================================
# pytest-html 钩子
# ============================================================

def pytest_html_report_title(report):
    """自定义 HTML 报告标题。"""
    report.title = "HarmonyOS UI Test Report"


def pytest_html_results_table_header(cells):
    """自定义报告表头。"""
    cells.pop()  # 移除 Links 列
    cells.insert(2, '<th class="sortable desc" data-column-type="string">Description</th>')
    cells.insert(0, '<th class="sortable" data-column-type="string">Feature</th>')


def pytest_html_results_table_row(report, cells):
    """自定义报告行 —— 插入 Feature 名称。"""
    cells.pop()
    cells.insert(2, f'<td>{"&nbsp;"}</td>')
    # 从 report 的 nodeid 中提取 feature 文件名
    feature_name = ""
    for part in report.nodeid.split("::"):
        if "features/" in part:
            feature_name = part.split("features/")[-1].replace(".feature", "")
            break
    cells.insert(0, f'<td>{feature_name}</td>')


