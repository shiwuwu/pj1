"""HTML 测试报告生成器 —— 展示 Feature → Scenario → Step 完整层级。"""

import re
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"


def ensure_report_dir() -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_DIR


# ============================================================
# 结果解析
# ============================================================

def _parse_results(output: str) -> dict:
    passed = failed = skipped = errors = 0
    m = re.search(r"(\d+)\s+passed", output)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", output)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+)\s+skipped", output)
    if m:
        skipped = int(m.group(1))
    m = re.search(r"(\d+)\s+errors?", output)
    if m:
        errors = int(m.group(1))
    return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors}


def _get_scenario_status(scenario_name: str, output: str) -> tuple[str, str]:
    """检查场景执行结果，返回 (status, error_msg)。"""
    safe = re.sub(r"\s+", "_", scenario_name)
    pattern = rf"(PASSED|FAILED)\s+.+test_{re.escape(safe)}\b"
    m = re.search(pattern, output)
    if not m:
        return ("unknown", "")
    status = "passed" if m.group(1) == "PASSED" else "failed"
    error_msg = ""
    if status == "failed":
        em = re.search(
            rf"FAILED\s+.+test_{re.escape(safe)}.+[\s\S]*?E\s+(.+?)(?:\n\n|\n\S|$)",
            output,
        )
        if em:
            error_msg = em.group(1).strip()[:300]
    return status, error_msg


# ============================================================
# 主入口
# ============================================================

def generate_summary_report(
    output_log: str,
    features_data: list[dict],
    duration_sec: float = 0,
) -> str:
    """解析 pytest 输出，生成按 Feature→Scenario→Step 展开的 HTML 报告。"""
    ensure_report_dir()
    results = _parse_results(output_log)

    # 给每个 scenario 注入执行结果
    for feat in features_data:
        for sc in feat["scenarios"]:
            status, error = _get_scenario_status(sc["name"], output_log)
            sc["status"] = status
            sc["error"] = error

    html = _render_html(results, features_data, duration_sec)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"test_report_{ts}.html"
    path.write_text(html, encoding="utf-8")
    logger.info(f"自定义报告已生成: {path}")
    return str(path)


# ============================================================
# HTML 模板
# ============================================================

def _render_html(results: dict, features: list[dict], duration: float) -> str:
    total = results["passed"] + results["failed"] + results["skipped"] + results["errors"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    feature_rows = ""
    for feat in features:
        feat_passed = sum(1 for s in feat["scenarios"] if s.get("status") == "passed")
        feat_total = len(feat["scenarios"])
        feat_badge = "✓" if feat_passed == feat_total else "✗"

        scenario_rows = ""
        for j, sc in enumerate(feat["scenarios"]):
            status = sc.get("status", "unknown")
            icon = {"passed": "✓", "failed": "✗", "unknown": "○"}.get(status, "○")
            row_class = f"scenario-{status}"

            # 步骤行
            step_rows = ""
            for step in sc.get("steps", []):
                keyword, content = _split_step(step)
                step_rows += f"""
                <tr class="step-row">
                    <td></td><td></td><td></td>
                    <td><span class="step-keyword {keyword.lower()}">{keyword}</span></td>
                    <td class="step-text">{content}</td>
                </tr>"""

            error_block = ""
            if sc.get("error"):
                error_block = f'<div class="scenario-error">⚠ {sc["error"]}</div>'

            scenario_rows += f"""
            <tr class="{row_class} scenario-toggle" data-target="sc-{_dom_id(sc['name'])}">
                <td></td>
                <td>{j + 1}</td>
                <td>{sc['name']}</td>
                <td colspan="2"><span class="badge {status}">{icon}</span> {error_block}</td>
            </tr>
            <tbody id="sc-{_dom_id(sc['name'])}" class="step-group">{step_rows}</tbody>"""

        feature_rows += f"""
        <tr class="feature-header" data-target="feat-{_dom_id(feat['name'])}">
            <td class="toggle-icon">▼</td>
            <td colspan="4"><strong>{feat['name']}</strong>
                <span style="color:#888;font-weight:normal;margin-left:10px">
                    {feat_passed}/{feat_total} 通过
                </span>
            </td>
        </tr>
        <tbody id="feat-{_dom_id(feat['name'])}" class="feature-group">{scenario_rows}</tbody>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarmonyOS 测试报告</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,"Microsoft YaHei",sans-serif; background:#f5f6fa; color:#2d3436; }}
.header {{ background:linear-gradient(135deg,#2d3436,#636e72); color:#fff; padding:28px 40px; }}
.header h1 {{ font-size:22px; font-weight:600; }}
.header .meta {{ margin-top:6px; font-size:13px; opacity:.75; }}
.container {{ max-width:1200px; margin:0 auto; padding:24px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:28px; }}
.card {{ background:#fff; border-radius:10px; padding:20px 24px; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
.card .num {{ font-size:36px; font-weight:700; }}
.card .label {{ font-size:13px; color:#888; margin-top:4px; }}
.card.total .num {{ color:#2d3436; }}
.card.passed .num {{ color:#00b894; }}
.card.failed .num {{ color:#d63031; }}
.card.rate .num {{ color:#0984e3; font-size:28px; }}
.progress-bar {{ background:#dfe6e9; border-radius:6px; height:10px; margin:0 0 28px; overflow:hidden; }}
.progress-bar .fill {{ background:linear-gradient(90deg,#00b894,#00cec9); height:100%; border-radius:6px; transition:width .4s; }}
h2 {{ font-size:17px; margin:24px 0 12px; color:#2d3436; }}
table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.06); margin-bottom:16px; }}
th {{ background:#2d3436; color:#fff; padding:10px 12px; font-size:13px; text-align:left; }}
td {{ padding:8px 12px; font-size:13px; border-bottom:1px solid #f0f0f0; vertical-align:middle; }}
.feature-header {{ cursor:pointer; background:#f8f9fa; }}
.feature-header:hover {{ background:#e9ecef; }}
.feature-header td {{ border-bottom:2px solid #ddd; }}
.toggle-icon {{ width:30px; text-align:center; font-size:12px; transition:transform .2s; }}
.toggle-icon.open {{ transform:rotate(-90deg); }}
.scenario-toggle {{ cursor:pointer; }}
.scenario-toggle:hover {{ background:#f1f2f6; }}
.scenario-failed {{ background:#fff5f5; }}
.step-row td {{ padding:4px 12px; font-size:12px; border-bottom:1px dotted #eee; }}
.step-keyword {{ display:inline-block; width:50px; padding:2px 6px; border-radius:3px; font-size:11px; font-weight:700; text-align:center; color:#fff; }}
.step-keyword.given {{ background:#0984e3; }}
.step-keyword.when {{ background:#e17055; }}
.step-keyword.then {{ background:#00b894; }}
.step-keyword.and {{ background:#636e72; }}
.step-keyword.but {{ background:#636e72; }}
.step-text {{ color:#555; }}
.badge {{ display:inline-block; width:26px; height:26px; line-height:26px; border-radius:50%; text-align:center; font-size:13px; font-weight:700; color:#fff; }}
.badge.passed {{ background:#00b894; }}
.badge.failed {{ background:#d63031; }}
.badge.unknown {{ background:#b2bec3; }}
.scenario-error {{ display:inline-block; color:#d63031; font-size:12px; margin-left:8px; max-width:500px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:middle; }}
.step-group {{ display:table-row-group; }}
.feature-group {{ display:table-row-group; }}
.footer {{ text-align:center; padding:20px; font-size:12px; color:#888; }}
</style>
</head>
<body>
<div class="header">
    <h1>HarmonyOS UI Test Report</h1>
    <div class="meta">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp; 耗时: {duration:.1f}s &nbsp;|&nbsp; 框架: Hypium + pytest-bdd</div>
</div>
<div class="container">
    <div class="cards">
        <div class="card total"><div class="num">{total}</div><div class="label">总计</div></div>
        <div class="card passed"><div class="num">{results["passed"]}</div><div class="label">通过</div></div>
        <div class="card failed"><div class="num">{results["failed"]}</div><div class="label">失败</div></div>
        <div class="card rate"><div class="num">{pass_rate:.1f}%</div><div class="label">通过率</div></div>
    </div>
    <div class="progress-bar"><div class="fill" style="width:{pass_rate}%"></div></div>
    <h2>Feature → Scenario → Step 明细</h2>
    <table>
        <thead><tr><th width="30"></th><th width="40">#</th><th>Scenario</th><th colspan="2">结果 / 步骤详情</th></tr></thead>
        {feature_rows}
    </table>
</div>
<div class="footer">Generated by HarmonyOS UI Test Runner &mdash; Hypium + pytest-bdd</div>
<script>
document.querySelectorAll('.feature-header').forEach(el => {{
    el.addEventListener('click', function() {{
        var tbody = document.getElementById(this.dataset.target);
        var icon = this.querySelector('.toggle-icon');
        if (tbody) {{
            tbody.style.display = tbody.style.display === 'none' ? 'table-row-group' : 'none';
            icon.classList.toggle('open');
        }}
    }});
}});
document.querySelectorAll('.scenario-toggle').forEach(el => {{
    el.addEventListener('click', function(e) {{
        var tbody = document.getElementById(this.dataset.target);
        if (tbody) {{
            tbody.style.display = tbody.style.display === 'none' ? 'table-row-group' : 'none';
        }}
    }});
}});
</script>
</body>
</html>"""


def _split_step(step: str) -> tuple[str, str]:
    """将 'When 启动应用 \"x\"' 拆分为 ('When', '启动应用 \"x\"')。"""
    m = re.match(r"^(Given|When|Then|And|But)\s+(.+)", step)
    if m:
        return m.group(1), m.group(2)
    return "", step


def _dom_id(text: str) -> str:
    """将文本转为安全的 DOM id。"""
    return re.sub(r"[^\w一-鿿]", "_", text)


