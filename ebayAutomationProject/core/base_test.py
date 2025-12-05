from playwright.sync_api import sync_playwright

class BaseTest:

    def __init__(self):

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def setup (self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False, slow_mo=1000,
            # this prevents getting stuck on the opening page of E-bay
            # where there's a security key setup coming from chrome.
            args=[
                "--disable-features=WebAuthentication",  # blocks Windows Hello
                "--disable-webauthn",  #  newer Chromium flag
                "--disable-usb-keyboard-detect",  # prevents security key prompt
                "--disable-extensions",
                "--disable-logging",
                "--disable-infobars"
            ]
        )

        self.context = self.browser.new_context()
        self.page = self.context.new_page()


    def teardown(self):

        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


    def get_page(self):
        return self.page