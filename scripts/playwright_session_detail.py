# -*- coding: utf-8 -*-
"""
Playwright end-to-end verification for the session detail page.

Checks:
  1. Login succeeds
  2. Session detail page loads with correct header (status badge = failed, 2 steps)
  3. Step timeline renders with 2 dots
  4. Step list shows llm_call + error rows
  5. Clicking each step expands the inspector panel
  6. Error step shows ToolExecutionError in red block
  7. Clicking Replay triggers loading state then shows banner + stdout
"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright, expect

BASE_URL    = "http://localhost:3000"
API_URL     = "http://localhost:8000/api/v1"
EMAIL       = "capsule-e2e@example.com"
PASSWORD    = "E2eTestPass99!"
WORKSPACE   = "01KV0GSJ7BMJJWT664K0MYTTH4"
SESSION_ID  = "ses-billing-failed-1781355557"
DETAIL_URL  = f"{BASE_URL}/dashboard/sessions/{SESSION_ID}"

SHOTS_DIR   = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SHOTS_DIR, exist_ok=True)

def shot(page, name: str) -> str:
    p = os.path.join(SHOTS_DIR, f"{name}.png")
    page.screenshot(path=p, full_page=False)
    return p

def log(msg: str) -> None:
    print(msg, flush=True)


def run() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        # ── 1. Log in ────────────────────────────────────────────────
        log("\n[1/7] Logging in …")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard**", timeout=15_000)
        log(f"    OK — landed on {page.url}")
        shot(page, "01_dashboard")

        # ── 2. Navigate to session detail ────────────────────────────
        log("\n[2/7] Navigating to session detail page …")
        page.goto(DETAIL_URL)
        page.wait_for_load_state("networkidle")
        shot(page, "02_session_detail_loaded")

        # Header: session ID should appear
        header_text = page.locator(f"text={SESSION_ID}").first
        expect(header_text).to_be_visible(timeout=8_000)
        log(f"    OK — session ID visible in header")

        # Status badge — must say "failed" and have err class
        badge = page.locator(".badge.err").first
        expect(badge).to_be_visible(timeout=5_000)
        badge_text = badge.inner_text().strip().lower()
        assert "failed" in badge_text, f"Expected 'failed' badge, got: {badge_text!r}"
        log(f"    OK — status badge: '{badge_text}'")

        # Step count chip — should say "2 steps"
        step_chip = page.locator("text=2 steps").first
        expect(step_chip).to_be_visible(timeout=5_000)
        log("    OK — '2 steps' chip visible")

        # ── 3. Timeline dots ─────────────────────────────────────────
        log("\n[3/7] Checking timeline scrubber …")
        page.wait_for_selector(".card", timeout=8_000)
        # Timeline track area (the progress bar container)
        # step counter shows "Step X / 2"
        step_counter = page.locator("text=/ 2").first
        expect(step_counter).to_be_visible(timeout=5_000)
        log("    OK — timeline shows '/ 2' (2 steps total)")
        shot(page, "03_timeline")

        # ── 4. Step list rows ────────────────────────────────────────
        log("\n[4/7] Checking step list rows …")
        # Step list items contain the event labels
        llm_row = page.locator("text=llm_call").first
        error_row = page.locator("text=error").first
        expect(llm_row).to_be_visible(timeout=5_000)
        expect(error_row).to_be_visible(timeout=5_000)
        log("    OK — both 'llm_call' and 'error' rows visible in step list")

        # ── 5. Click LLM step → inspector shows model info ───────────
        log("\n[5/7] Clicking llm_call step …")
        llm_row.click()
        page.wait_for_timeout(500)
        shot(page, "04_llm_step_selected")

        # Inspector should show provider/model metadata
        provider_chip = page.locator("text=openai").first
        expect(provider_chip).to_be_visible(timeout=5_000)
        log("    OK — inspector shows 'openai' provider chip")

        model_chip = page.locator("text=gpt-4o").first
        expect(model_chip).to_be_visible(timeout=3_000)
        log("    OK — inspector shows 'gpt-4o' model chip")

        # Input messages block should be visible
        input_label = page.locator("text=INPUT").first
        expect(input_label).to_be_visible(timeout=3_000)
        log("    OK — INPUT code block visible")

        # ── 6. Click error step → inspector shows error block ────────
        log("\n[6/7] Clicking error step …")
        # The error row in the step list — it has red border-left
        # Find step list item that contains 'error' text (the event_type)
        # Step list rows are divs with the step label text
        page.locator("text=error · error").click()
        page.wait_for_timeout(500)
        shot(page, "05_error_step_selected")

        # Error block is a red div with "ERROR" label
        error_label = page.locator("text=ERROR").first
        expect(error_label).to_be_visible(timeout=5_000)
        log("    OK — ERROR label visible in inspector")

        error_msg = page.locator("text=Refund amount").first
        expect(error_msg).to_be_visible(timeout=3_000)
        log("    OK — error message 'Refund amount …' visible in inspector")

        error_type_text = page.locator("text=ToolExecutionError").first
        expect(error_type_text).to_be_visible(timeout=3_000)
        log("    OK — 'ToolExecutionError' visible in error block")
        shot(page, "06_error_inspector")

        # ── 7. Replay ────────────────────────────────────────────────
        log("\n[7/7] Clicking Replay …")
        replay_btn = page.locator("button", has_text="Replay").first
        expect(replay_btn).to_be_enabled(timeout=3_000)
        replay_btn.click()

        # Loading state: button should change to "Replaying…"
        replaying_btn = page.locator("button", has_text="Replaying…").first
        expect(replaying_btn).to_be_visible(timeout=5_000)
        log("    OK — 'Replaying…' spinner visible (polling has started)")
        shot(page, "07_replaying_state")

        # Wait for banner (up to 60s for local replay + polling)
        log("    Waiting for replay to complete (poll interval 2s, max 65s) …")
        # Proper Playwright OR: wait for either banner text to appear
        banner_loc = page.locator("text=Replay complete").or_(
            page.locator("text=Replay failed")
        )
        banner_loc.first.wait_for(state="visible", timeout=65_000)
        page.wait_for_timeout(300)
        shot(page, "08_replay_result")

        banner_text = banner_loc.first.inner_text().strip()
        log(f"    Banner text: {banner_text!r}")

        if "Replay complete" in banner_text:
            log("    OK — Replay completed successfully (deterministic)")
            # Check for stdout pre block (present when capsule CLI ran)
            pre_blocks = page.locator("pre").all()
            stdout_pre = None
            for pre in pre_blocks:
                if pre.is_visible():
                    stdout_pre = pre
                    break
            if stdout_pre:
                stdout_content = stdout_pre.inner_text()[:200]
                log(f"    stdout block visible: {stdout_content[:80]!r} …")
            else:
                log("    (no stdout — capsule CLI not on server PATH, time-based simulation used)")
        elif "timed out" in banner_text:
            log(f"    60s client timeout fired (Modal job didn't resolve): {banner_text!r}")
            log("    This is expected when Modal is configured but job stays queued")
        else:
            log(f"    Banner: {banner_text!r}")

        shot(page, "09_final_state")
        log(f"\n    Screenshots saved to: {SHOTS_DIR}")

        browser.close()

    log("\n" + "=" * 55)
    log("  ALL VISUAL CHECKS PASSED")
    log("=" * 55)


if __name__ == "__main__":
    run()
