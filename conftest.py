"""项目根 conftest —— 注册 --lang 选项并生成对应语言的 Gherkin 文件。"""

import os


def pytest_addoption(parser):
    parser.addoption(
        "--lang", action="store", default="all",
        choices=["zh_CN", "zh_TW", "en", "all"],
        help="测试语言: zh_CN(简中) / zh_TW(繁中) / en / all(全部)",
    )


def pytest_configure(config):
    lang = config.getoption("--lang", default="all")
    os.environ["TEST_LANG"] = lang

    # 根据 --lang 生成对应语言的 .feature 文件
    import shutil
    from testcases.steps.step_patterns import generate_features, GENERATED_DIR

    # 先清空旧的生成文件
    if GENERATED_DIR.exists():
        shutil.rmtree(GENERATED_DIR)

    langs = [lang] if lang != "all" else ["zh_CN", "zh_TW", "en"]
    for l in langs:
        generate_features(l)

    # 设置 pytest-bdd 的 features 搜索路径
    if lang == "all":
        config.inicfg["bdd_features_base_dir"] = str(GENERATED_DIR)
    else:
        config.inicfg["bdd_features_base_dir"] = str(GENERATED_DIR / lang)
