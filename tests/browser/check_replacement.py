"""Click the evidence-replacement workflow on invented data in a fresh store.

Run with a Python environment containing playwright and its Chromium browser:
    python tests/browser/check_replacement.py --out .tmp/replacement-check
Build apps/workbench-ui first. No existing engagement is opened or changed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PID = "ap.payment_voucher_reference"
VOUCHERS = (
    "Voucher Number,Vendor Number,Invoice Number,Voucher Date,Voucher Amount\n"
    "V1,VEN-1,INV-100,2025-11-03,1200.00\n"
    "V2,VEN-2,INV-200,2025-11-10,450.00\n"
    "V3,VEN-1,INV-101,2025-11-20,800.00\n"
)
PAYMENTS = (
    "Payment Number,Vendor Number,Voucher Number,Payment Amount,Payment Date\n"
    "P1,VEN-1,V1,1200.00,2025-11-15\n"
    "P2,VEN-2,V2,450.00,2025-11-25\n"
    "P3,VEN-1,V3,800.00,2025-12-05\n"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0, help="0 chooses an unused port")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name, content in (("vouchers.csv", VOUCHERS), ("payments.csv", PAYMENTS),
                          ("vouchers_revised.csv", "\n".join(VOUCHERS.splitlines()[:3]) + "\n")):
        (out / name).write_text(content, encoding="utf-8")
    env = dict(os.environ, PYTHONUTF8="1")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(p / "src") for p in (ROOT / "packages").iterdir() if (p / "src").is_dir()]
        + [str(ROOT / "apps/workbench-api")])
    checks = []
    with (out / "server.log").open("w", encoding="utf-8") as server_log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "workbench_api", "--data", str(out / "store"), "--port", str(args.port)],
            cwd=ROOT, env=env, stdout=server_log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError("Workbench exited; inspect server.log")
                started = re.search(r"workbench:\s+(http://127\.0\.0\.1:\d+/)",
                                    (out / "server.log").read_text(encoding="utf-8"))
                if not started:
                    time.sleep(0.2)
                    continue
                url = started.group(1)
                try:
                    with urllib.request.urlopen(url, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("Workbench did not start")
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1500, "height": 1000})
                page_errors = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                page.set_default_timeout(15000)

                def capture(name):
                    page.screenshot(path=str(out / f"{name}.png"), full_page=True)
                    text = "\n".join(line.rstrip() for line in page.locator("main").inner_text().splitlines()) + "\n"
                    (out / f"{name}.txt").write_text(text, encoding="utf-8")

                def tab(name):
                    page.locator("nav.tabs").get_by_role("button", name=name, exact=True).click()

                def upload(name, role, replace=False):
                    page.locator('form.inline input[type="file"]').first.set_input_files(str(out / name))
                    page.get_by_role("button", name="upload sources", exact=True).click()
                    row = page.locator("tr").filter(has=page.get_by_text(name, exact=True)).first
                    expect(row).to_be_visible()
                    row.locator("select").select_option(role)
                    row.get_by_role("button", name="confirm mapping", exact=True).click()
                    if replace:
                        page.get_by_role("button", name="replaces it", exact=True).click()
                    else:
                        page.get_by_role("button", name="load", exact=True).click()
                    expect(page.get_by_text("loaded ✓", exact=True)).to_have_count(3 if replace else (1 if role == "Vouchers" else 2))

                page.goto(url)
                page.get_by_placeholder("client name").fill("Invented Hardware Co — replacement check")
                page.get_by_label("period end").fill("2025-12-31")
                page.get_by_role("button", name="create engagement", exact=True).click()
                page.get_by_role("button", name="open", exact=True).first.click()
                tab("Sources & Mappings")
                upload("vouchers.csv", "Vouchers")
                upload("payments.csv", "Payments")
                capture("01-loaded")
                tab("Runs & Findings")
                page.locator("form.inline select").first.select_option(PID)
                page.get_by_role("button", name="run", exact=True).click()
                run_rows = page.locator("table.dense").first.locator("tbody tr")
                expect(run_rows).to_have_count(1)
                expect(run_rows.first).to_contain_text("completed")
                expect(run_rows.first).not_to_contain_text("stale:")
                expect(page.get_by_text("showing 0 of 0")).to_be_visible()
                capture("02-clean-run")
                checks.append("Initial payment-to-voucher run completes with zero findings.")

                tab("Sources & Mappings")
                upload("vouchers_revised.csv", "Vouchers", replace=True)
                expect(page.locator("main")).to_contain_text("not used: a later Vouchers load replaces it")
                capture("03-replaced")
                checks.append("Revised voucher file replaces the loaded file through the UI.")
                tab("Runs & Findings")
                expect(run_rows.first).to_contain_text("stale:")
                capture("04-stale-run")
                checks.append("Original run visibly becomes stale after replacement.")
                tab("What Changed")
                expect(page.locator("main")).to_contain_text("vouchers_revised.csv")
                removed = page.locator("tr").filter(has_text="removed").filter(has_text="V3")
                expect(removed).to_have_count(1)
                expect(removed).to_contain_text("800.00")
                card = page.locator(".impact-card").filter(has_text="P3")
                expect(card).to_have_count(1)
                expect(card).to_contain_text(PID)
                expect(card).to_contain_text("needs a disposition")
                expect(page.get_by_role("button", name="rerun", exact=True)).to_have_count(1)
                capture("05-what-changed")
                checks.append("What Changed identifies removed V3 (800.00) and previews a new P3 finding.")
                page.get_by_role("button", name="rerun", exact=True).click()
                expect(page.locator("main")).to_contain_text("None: every run already used the current files.")
                capture("06-rerun-from-impact")
                tab("Runs & Findings")
                expect(run_rows).to_have_count(2)
                current_run = run_rows.filter(has_not_text="stale:")
                historical_run = run_rows.filter(has_text="stale:")
                expect(current_run).to_have_count(1)
                expect(current_run).to_contain_text("completed")
                expect(historical_run).to_have_count(1)
                expect(page.get_by_text("showing 1 of 1")).to_be_visible()
                expect(page.locator("main")).to_contain_text("P3")
                expect(page.locator("main")).to_contain_text("V3")
                capture("07-current-finding")
                assert page_errors == [], page_errors
                checks.append("Rerun from What Changed produces one current P3/V3 finding; old run stays historical.")
                checks.append("No uncaught browser page errors.")
                browser.close()
            (out / "result.json").write_text(json.dumps({"passed": True, "checks": checks}, indent=2), encoding="utf-8")
            print(json.dumps({"passed": True, "evidence": str(out), "checks": checks}, indent=2))
            return 0
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
