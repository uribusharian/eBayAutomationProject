
from playwright.sync_api import sync_playwright
import base64
from pathlib import Path
import pytest
from pytest_html import extras

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    #attach screenshots from photos folder to report
    outcome = yield
    report = outcome.get_result()

    # attach only during the main test phase
    if report.when != "call":
        return

    photos_dir = Path("photos")
    if not photos_dir.exists():
        return

    extra = getattr(report, "extra", [])

    for screenshot in sorted(photos_dir.glob("product_*.png")):
        try:
            with screenshot.open("rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            # use PNG helper with base64 string
            extra.append(extras.png(b64_data))

        except Exception as e:
            print(f"[WARN] Failed to attach screenshot {screenshot}: {e}")

    report.extra = extra

@pytest.fixture
def page():

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=1000,
            args=[
                "--disable-features=WebAuthentication", # blocks Windows Hello
                "--disable-webauthn",  # newer Chromium flag
                "--disable-usb-keyboard-detect", # prevents security key prompt
                "--disable-extensions",
                "--disable-logging",
                "--disable-infobars",
                "--start-maximized"  # start browser in maximized window
            ]
        )
        # Create a new context
        # ensure elements are visible during tests.
        context = browser.new_context()
        page = context.new_page()

        # Ensure the page is also set to the same viewport size.
        try:
            page.set_viewport_size({"width": 1920, "height": 1080})
        except Exception:
            pass

        # Give the test a usable page object
        yield page

        # Cleanup after the test
        context.close()
        browser.close()