#!/usr/bin/env python3
"""
US05 – Alertas por Vencimiento y Garantía
General test runner

Usage
-----
    # All automated tests (default)
    python run_tests.py

    # Specific test group
    python run_tests.py --group licencias
    python run_tests.py --group garantias
    python run_tests.py --group eol
    python run_tests.py --group config

    # By marker
    python run_tests.py --marker sistema
    python run_tests.py --marker integracion

    # Generate HTML report (always saved to reports/)
    python run_tests.py --report

    # Verbose
    python run_tests.py -v

Prerequisites
-------------
    1. Copy .env.example to .env and fill in your values.
    2. pip install -r requirements.txt
    3. Docker running with Snipe-IT (proyecto_qa-app-1).
    4. Set SNIPEIT_ARTISAN_PREFIX in .env if your container name differs.
"""
import subprocess
import sys
import argparse
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent

GROUP_MAP = {
    "licencias": "automated/test_hu05_01_03_licencias_umbral.py",
    "garantias": "automated/test_hu05_04_07_garantias_activos.py",
    "eol":       "automated/test_hu05_08_10_eol_archivado.py",
    "config":    "automated/test_hu05_11_13_config_scheduler.py",
}


def build_cmd(args) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]

    if args.group:
        target = GROUP_MAP.get(args.group)
        if not target:
            print(f"[error] Unknown group '{args.group}'. Valid: {list(GROUP_MAP)}")
            sys.exit(1)
        cmd.append(target)
    else:
        cmd.append("automated/")

    if args.marker:
        cmd += ["-m", args.marker]

    if args.verbose:
        cmd.append("-v")
    else:
        cmd += ["-v", "--tb=short"]

    if args.report:
        report_name = f"reports/{date.today().isoformat()}_US05_execution_report.html"
        cmd += [f"--html={report_name}", "--self-contained-html"]
        print(f"[info] Report will be saved to: {report_name}")

    return cmd


def main():
    parser = argparse.ArgumentParser(description="US05 test runner")
    parser.add_argument("--group", choices=list(GROUP_MAP),
                        help="Run a specific test group")
    parser.add_argument("--marker", help="Run tests with a specific marker (sistema, integracion, etc.)")
    parser.add_argument("--report", action="store_true",
                        help="Generate HTML report in reports/")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    cmd = build_cmd(args)
    print(f"[run] {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=HERE)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
