"""从 locales/ 加载翻译，提供多语言步骤匹配 + 模板渲染。

模板语法（feature 文件中使用）:
    @key_name                    → 无参步骤
    @key_name("arg1", "arg2")    → 带参步骤

渲染引擎根据 locale 将 @key 替换为对应语言的 Gherkin 步骤文本。
"""

import json
import re
import shutil
from pathlib import Path

from pytest_bdd import parsers

LOCALE_DIR = Path(__file__).resolve().parent.parent.parent / "locales"
FEATURE_DIR = Path(__file__).resolve().parent.parent / "features"
GENERATED_DIR = FEATURE_DIR / ".generated"

_LOCALES: dict[str, dict] = {}
_TPL_RE = re.compile(r'@(\w+)(?:\(((?:"[^"]*")(?:\s*,\s*"[^"]*")*)\))?')


def _load() -> dict[str, dict]:
    global _LOCALES
    if not _LOCALES:
        for fp in sorted(LOCALE_DIR.glob("*.json")):
            _LOCALES[fp.stem] = json.loads(fp.read_text(encoding="utf-8"))
    return _LOCALES


# ============================================================
# 步骤匹配（用于步骤定义装饰器）
# ============================================================

def all_of(key: str) -> list:
    """返回所有语言的 parsers.parse() 列表，用于 @given/@when/@then 装饰器。"""
    locales = _load()
    patterns = []
    for lang in sorted(locales):
        text = locales[lang].get(key, "")
        if text and text not in patterns:
            patterns.append(text)
    return [parsers.parse(p) for p in patterns]


# ============================================================
# 模板渲染 —— 将 @key 模板转为具体语言的 Gherkin 文件
# ============================================================

def generate_features(lang: str):
    """根据 locale 生成 .generated/{lang}/ 下的 Gherkin 文件。

    读取 features/*.feature 模板，将 @key("arg") 替换为 locale 文本，
    输出到 .generated/{lang}/ 同名文件。
    """
    locales = _load()
    if lang not in locales:
        raise ValueError(f"未知语言: {lang}，可用: {list(locales)}")

    out_dir = GENERATED_DIR / lang
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for tpl_path in sorted(FEATURE_DIR.glob("*.feature")):
        content = tpl_path.read_text(encoding="utf-8")
        rendered = _render(content, lang)
        (out_dir / tpl_path.name).write_text(rendered, encoding="utf-8")

    return out_dir


def generated_path(lang: str) -> str:
    return str(GENERATED_DIR / lang)


def _render(template: str, lang: str) -> str:
    """将模板中的 @key("arg") 替换为对应语言的步骤文本。"""
    locale = _load()[lang]

    def _replacer(m: re.Match) -> str:
        key = m.group(1)
        args_str = m.group(2)  # 如 '"arg1", "arg2"'
        pattern = locale.get(key)
        if not pattern:
            return f"# [未翻译: {key}]"

        if args_str:
            # 解析参数: '"a", "b"' → ['a', 'b']
            args = [a.strip().strip('"') for a in args_str.split(",")]
            # 按占位符 {xxx} 的顺序逐个替换
            placeholders = re.findall(r"\{(\w+)\}", pattern)
            for i, ph in enumerate(placeholders):
                if i < len(args):
                    pattern = pattern.replace(f"{{{ph}}}", args[i], 1)
        return pattern

    return _TPL_RE.sub(_replacer, template)
