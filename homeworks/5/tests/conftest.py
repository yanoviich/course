import json
from pathlib import Path

RESULTS = []


def pytest_runtest_logreport(report):
    if report.when == "call":
        RESULTS.append({
            "test": report.nodeid,
            "status": "PASS" if report.passed else "FAIL",
            "details": "" if report.passed else str(report.longrepr),
        })


def pytest_sessionfinish(session, exitstatus):
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    (report_dir / "security_report.json").write_text(
        json.dumps(RESULTS, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# Security test report",
        "",
        f"Total: {len(RESULTS)}",
        f"PASS: {sum(1 for x in RESULTS if x['status'] == 'PASS')}",
        f"FAIL: {sum(1 for x in RESULTS if x['status'] == 'FAIL')}",
        "",
        "| Test | Status |",
        "|---|---|",
    ]
    for item in RESULTS:
        lines.append(f"| `{item['test']}` | **{item['status']}** |")

    (report_dir / "security_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
