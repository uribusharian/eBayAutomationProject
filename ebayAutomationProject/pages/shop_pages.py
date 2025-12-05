import re
import selectors
from abc import ABC, abstractmethod
from typing import List

from pytest_base_url.plugin import base_url

from utils.price_parser import parse_price_to_number
from core import config
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

logger = logging.getLogger(__name__)

class BasePage(ABC):

    def __init__(self, page):
        self.page = page

    @abstractmethod
    def is_loaded(self) -> bool:
        pass

    def goto(self, url):
        self.page.goto(url)

    def wait_for_visible(self, locator:str):
        # wait until the element of the locator is visible
        self.page.locator(locator).wait_for(state="visible")

    def click(self,locator:str):
        self.page.locator(locator).click()

    def fill (self, locator:str , text:str):
        self.page.locator(locator).fill(text)

    def get_attribute(self, locator:str, name:str):
        return self.page.locator(locator).get_attribute(name)

    def get_text(self, locator:str):
        return self.page.locator(locator).inner_text().strip()


class HomePage(BasePage):

    def __init__(self, page):
        super().__init__(page)

    def is_loaded(self):

        try:
            self.wait_for_visible("input#gh-ac")
            return True
        except PlaywrightError:
            # only playwright errors are expected here (timeouts?)
            return False

    def _dismiss_homepage_popups(self):

        # try to avoid popups with common selectors
        selectors = [
            "button#gdpr-banner-accept",
            "button[aria-label='Accept all']",
            "button:has-text('Accept')",
            "button:has-text('Got it')",
            "button:has-text('הבנתי')",
            "button[aria-label='Close']",
            "button:has-text('Close')",
            "button#dialog-close",
            "button#siNoThrottle",
            "button[aria-label='No thanks']",
        ]
        for select in selectors:
            try:
                some_locator = self.page.locator(select)
                if some_locator.count() and some_locator.first.is_visible():
                    some_locator.first.click()
                    #allow dialog to close
                    self.page.wait_for_timeout(500)
            except (PlaywrightError, AttributeError, TypeError):
                continue


    def enter_search_term(self, query:str):

        self.fill("input#gh-ac", query)


    def submit_search(self):
        # not every place in eBay use input elements
        #that is why i try several seletors

        clicked = False

        candidates = [
            "input#gh-btn",
            "button#gh-btn",
            "button.btn-prim"
        ]

        for candidate in candidates:
            try:
                some_locator = self.page.locator(candidate)
                if some_locator.count() and some_locator.first.is_enabled():
                    some_locator.first.click()
                    clicked = True
                    break
            except (PlaywrightError, AttributeError, TypeError):
                continue
        #if it does not work, fallback to pressing "Enter"
        if not clicked:
            try:
                search_input = self.page.locator("input#gh-ac")
                if search_input.count() and search_input.first.is_enabled():
                    search_input.first.press("Enter")
                    clicked = True
                else:
                    self.page.keyboard.press("Enter")
                    clicked = True
            except (PlaywrightError, AttributeError, TypeError):
                pass
        #if none os working just raise TimeoutError
        if not clicked:
            raise TimeoutError("Search button not found or not clickable on the home page")

# Navigate to the home page and dismiss any cookie/region popups
    def search_for(self, query:str):

        try:
            self.goto(config.get_base_url())
        except PlaywrightError:
            # if the navigation fails continue on current page
            pass
        #dismiss popups before using search feild
        self._dismiss_homepage_popups()
        #wait for search feild - visible
        self.is_loaded()
        # write in seach field and click searh
        self.enter_search_term(query)
        # dismiss popups after using search feild
        self._dismiss_homepage_popups()
        self.submit_search()

        return SearchResultsPage(self.page)

class LoginPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

    def is_loaded(self) -> bool:
        try:
            self.wait_for_visible("input#userid")
            return True
        except PlaywrightError:
            return False

    def open(self):

        self.goto("https://signin.ebay.com/")
        self.is_loaded()

    def enter_username(self, username:str):

    # try to fill the username/email field using several possible selectors
        selectors = [
            "input#userid",
            "input[name='userid']",
            "input#signin-username",
            "input[name='email']",
            "input#email",
            "input[type='email']"
        ]

        for selector in selectors:
            try:
                some_locator = self.page.locator(selector)
                if some_locator.count() and some_locator.first.is_enabled():
                    some_locator.first.fill(username)
                    return
            except (PlaywrightError, AttributeError, TypeError):
                continue

        #fallback - fill the first visible input
        try:
            some_locator = self.page.locator("input")
            if some_locator.count():
                some_locator.first.fill(username)
        except (PlaywrightError, AttributeError, TypeError):
            pass

    # try to fill the password field using several possible selectors
    def enter_password(self, password:str):

        selectors = [
            "input#pass",
            "input[name='pass']",
            "input[name='password']",
            "input#password",
            "input[type='password']"
        ]
        for selector in selectors:
            try:
                some_locator = self.page.locator(selector)
                if some_locator.count() and some_locator.first.is_enabled():
                    some_locator.first.fill(password)
                    return
            except (PlaywrightError, AttributeError, TypeError):
                continue
        # fallback - type into any input of type password
        try:
            some_locator = self.page.locator("input[type='password']")
            if some_locator.count():
                some_locator.first.fill(password)
        except (PlaywrightError, AttributeError, TypeError):
            pass

    def submit_login(self):
        self.click("button#sgnBt")

    def _dismiss_initial_popups(self):
        # try to avoid popups with common selectors

        selectors = [
            "button#gdpr-banner-accept",
            "button[aria-label='Accept all']",
            "button:has-text('Accept')",
            "button:has-text('Got it')",
            "button:has-text('הבנתי')",
            "button[aria-label='Close']",
        ]
        for selector in selectors:
            try:
                some_locator = self.page.locator(selector)
                if some_locator.count() and some_locator.first.is_visible():
                    some_locator.first.click()
                    self.page.wait_for_timeout(500)
            except (PlaywrightError, AttributeError, TypeError):
                continue

    def _handle_post_login_flow(self):

        # it handles screens that appear after inserting a password
        selectors = [
            "button:has-text('Continue')",
            "button:has-text('Go to eBay')",
            "button:has-text('Not now')",
            "button:has-text('No thanks')",
            "button:has-text('המשך')",
        ]
        for sel in selectors:
            try:
                loc = self.page.locator(sel)
                if loc.count() and loc.first.is_visible():
                    loc.first.click()
                    self.page.wait_for_timeout(1000)
                    break
            except (PlaywrightError, AttributeError, TypeError):
                continue

    def login_full_seq(self, username:str, password:str):

        self.open()
        self._dismiss_initial_popups()

        try:
            #if we detect we are looged in try landing on the home Page
            if self.is_logged_in():
                try:
                    base_url = config.get_base_url()
                except (ImportError, AttributeError):
                    base_url = "https://www.ebay.com"

                try:
                    self.goto(base_url)
                    self._dismiss_initial_popups()
                    self._close_post_login_popups()
                except PlaywrightError:
                    pass
                return True
        except PlaywrightError:
            pass

        self.enter_username(username)

        continue_selectors = [
            "button#signin-continue-btn",
            "button[type='submit'][id*='signin-continue']",
            "button:has-text('Continue')",
            "button:has-text('המשך')",
        ]
        try:
            for selector in continue_selectors:
                some_locator = self.page.locator(selector)
                if some_locator.count() and some_locator.first.is_visible():
                    some_locator.first.click()

                    try:
                        self.page.wait_for_selectors(
                            "input#pass, input[name='pass'], input[name='password'], input#password, input[type='password']",
                            timeout=10000
                        )
                    except PlaywrightError:
                        pass
                    break
        except PlaywrightError:
            pass

        self.enter_password(password)
        self.submit_login()

        #for window "Simplify your sign‑in" with the "Skip for now"
        try:
            skip = self.page.locator("text=Skip for now")
            if skip.count() and skip.first.is_visible():
                skip.first.click()
                self.page.wait_for_timeout(1000)
        except PlaywrightError:
            pass

        self._handle_post_login_flow()
        self._handle_additional_security
        self._close_post_login_popups()

        # wait for page to update.
        self.page.wait_for_timeout(2000)
        try:
            base_url = config.get_base_url()
        except (ImportError, AttributeError):
            #fallback
            base_url = "https://www.ebay.com"

        try:
            self.page.goto(base_url)
            self._dismiss_initial_popups()
            self._close_post_login_popups()
        except PlaywrightError:
            pass

        #if we are still not singed in - the login was not successful
        if self.page.url.startswith("https://signin.ebay."):
            return False

        return self.is_logged_in()

    def _click_continue_button(self):

        candidates = [
            "button#signin-continue-btn",
            "button#signin-continue-link",
            "button[aria-label='Continue']",
            "button[type='submit'][data-role='continue']"
        ]
        for selector in candidates:
            try:
                btn = self.page.locator(selector)
                if btn.is_visible():
                    btn.click()
                    self.page.wait_for_timeout(500)
                    return
            except (PlaywrightError, AttributeError, TypeError):
                continue

    def _handle_additional_security(self):

        #handle remember me or stay signed in problems
        try:
            btn = self.page.locator("button:has-text('Yes'), button:has-text('Continue'), button:has-text('OK')")
            if btn.is_visible():
                btn.click()
                self.page.wait_for_timeout(500)
        except PlaywrightError:
            pass

        # Handle region or currency confirmation problems
        try:
            region_btn = self.page.locator("button:has-text('Save'), button:has-text('Confirm'), button:has-text('Continue shopping')")
            if region_btn.is_visible():
                region_btn.click()
                self.page.wait_for_timeout(500)
        except PlaywrightError:
            pass

        try:
            if self.page.locator("input#securityCode, input[name='securityCode']").is_visible():

                return
        except PlaywrightError:
            pass

    def _close_post_login_popups(self):

        close_selectors = [
            "button[aria-label='Close']",
            "button[aria-label='Skip for now']",
            "button[title='Close']",
            "button#gdpr-banner-accept",
            "button:has-text('Close')",
            "button:has-text('Got it')",
            "button#dialog-close",
            "button#siNoThrottle",
            "button[aria-label='No thanks']"
        ]
        for selector in close_selectors:
            try:
                btn = self.page.locator(selector)
                if btn.is_visible():
                    btn.click()
                    # Wait a moment for the modal to disappear
                    self.page.wait_for_timeout(500)
                    break
            except (PlaywrightError, AttributeError, TypeError):
                continue

    def is_logged_in(self) -> bool:

        account_selectors = [
            "#gh-ug",  # classic greeting container
            "a[title*='My eBay']",
            "a[aria-label*='My eBay']",
            "button[aria-label*='My eBay']",
            "a[aria-label*='חשבון']",
            "button[aria-label*='חשבון']",
        ]
        try:
            # if greeting is visible assume logged in
            for selector in account_selectors:
                some_locator = self.page.locator(selector)
                if some_locator.count() and some_locator.first.is_visible():
                    return True
            # If we  see  sign in url or username assume not logged in
            if self.page.url.startswith("https://signin.ebay."):
                return False
            if self.page.locator("input#userid").count():
                return False

            return True
        except PlaywrightError:
            return False

class SearchResultsPage(BasePage):

    def is_loaded(self):
        try:
            # common locators
            self.wait_for_visible("main, #mainContent, ul.srp-results")
            return True
        except PlaywrightError:
            return False

    def apply_max_price_filter(self, max_price:float):
        try:
            max_input = self.page.locator("input[name='_udhi']")
            if max_input.count():
                max_input.first.fill(str(int(max_price)))
                # press Enter after inserting max parice
                max_input.first.press("Enter")
                self.is_loaded()
        except PlaywrightError:
            #if filter is not available just continue
            pass

    def get_item_cards_on_page(self):
       #i did not succeed with css locators so i will collect href that contains /itm/
        links = self.page.locator("a[href*='/itm/']")
        count = links.count()

        handles = []
        for index in range(count):
            link = links.nth(index)
            try:
                href = link.get_attribute("href")
            except PlaywrightError:
                href = None
            if not href:
                continue
            # filters out placeholder links takes only /itm/with 8 numbers after
            matched_link = re.search(r"/itm/(\d{8,})", href)
            if not matched_link:
                continue
            handles.append(link)

        print(
            f"get_item_cards_on_page: "
            f"found  product links with href*='/itm/'"
        )
        return handles

    def extract_item_price(self, item_element):
        #get father li item
        try:
            li = item_element.query_selector(
                "xpath=ancestor::li[contains(@class, 's-item')]"
            )
        except (PlaywrightError, AttributeError):
            li = None

        root = li or item_element

        price_selectors = [
            ".s-item__price",
            ".s-item__detail span.s-item__price",
            "span[aria-label*='Price']",
            "span[aria-label*='Current bid']",
            "span[aria-label*='Buy It Now']",
        ]

        for selector in price_selectors:
            try:
                el = root.query_selector(selector)
                if not el:
                    continue
                text = el.inner_text().strip()
                value = parse_price_to_number(text)
                if value and value > 0:
                    return value
            except (PlaywrightError, AttributeError, ValueError, TypeError):
                # ignore failures to parse or access price element
                continue

        return None

# try returning a product href
    def extract_item_url(self, item_element):
        try:
            href = item_element.get_attribute("href")
            return href
        except (PlaywrightError, AttributeError):
            return None

    def _get_any_item_urls_on_page(self, limit: int) -> List[str]:
        #fallback for returning up to limit from the result page
        urls: List[str] = []

        for link in self.get_item_cards_on_page():
            if len(urls) >= limit:
                break
            url = self.extract_item_url(link)
            if url:
                urls.append(url)

        print(
            f" _get_any_item_urls_on_page: returning "
            f" URLs (limit={limit})"
        )
        return urls

    def get_items_under_price_on_page(self, max_price:float):

        #collect urls on the current page. do not enforce max_price
        # alwqays returns a list (possibly empty)

        urls: list[str] = []

        for link in self.get_item_cards_on_page():
            url = self.extract_item_url(link)
            if url:
                urls.append(url)

        print(
            f" get_items_under_price_on_page: returning "

        )
        return urls

    def has_next_page(self):
        try:
            next_button = self.page.locator(
                "a.pagination__next, a[aria-label^='Next']"
            )
            if not next_button or next_button.count() == 0:
                return False
            return next_button.first.is_enabled()
        except PlaywrightError:
            return False

    def collect_items_under_price_across_pages(self, max_price:float, limit:int):

        #collecting the "limit" uurls found on each page. if no items found using the price filter uses a fallback to get
        #any urls and still enforces the max_cart_total after item are added to cart
        collected: List[str] = []

        seen: set[str] = set()

        def _add_unique(urls: List[str]):
            # adds urls to the list if not already seen
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    collected.append(url)
                    if len(collected) >= limit:
                        break

        # try to collect from the current page
        page_urls = self.get_items_under_price_on_page(max_price)
        _add_unique(page_urls)

        #fall back to any items on this page
        if not collected:
            print(
                f"No items found under price {max_price}; "
                f"falling back to first results without price filter"
            )
            fallback_urls = self._get_any_item_urls_on_page(limit)
            _add_unique(fallback_urls)

        # optionally if we still need more and there is a next page run on
        # the pages until limit (right now hard coded to 5)
        max_pages = 5
        pages_visited = 1
        while len(collected) < limit and pages_visited < max_pages and self.has_next_page():
            try:
                self.page.locator("a.pagination__next, a[aria-label^='Next']").first.click()
                self.is_loaded()
                pages_visited += 1

                page_urls = self.get_items_under_price_on_page(max_price)
                _add_unique(page_urls)

                if len(collected) >= limit:
                    break

                if not page_urls:
                    # using fallback for this page too
                    remaining = limit - len(collected)
                    if remaining <= 0:
                        break
                    fallback_urls = self._get_any_item_urls_on_page(remaining)
                    _add_unique(fallback_urls)
            except PlaywrightError:
                break

        print(
            f"collect_items_under_price_across_pages: "
            f"final collected {len(collected)} URLs (limit={limit})"
        )
        return collected

class ProductPage(BasePage):
# Provides helpers for opening product url, read its price, and add it to cart

    def __init__(self, page):
        super().__init__(page)

    def _try_select_simple_variations(self) -> None:

       # try to select simple size\colors - ignore non-valid options
        logger.debug(" Trying to select simple variations (size/color/etc.)")

        #<select> dropdowns
        try:
            selects = self.page.locator("select")

            for i in range(selects.count()):
                select = selects.nth(i)
                if not select.is_visible():
                    continue

                # select the first non-disabled, non-empty option
                options = select.locator("option:not([disabled]):not([value=''])")
                if options.count() == 0:
                    continue

                # of already a value selected
                try:
                    current_value = select.input_value()
                except (PlaywrightError, AttributeError):
                    current_value = None

                if current_value:
                    continue

                first = options.first
                value = first.get_attribute("value")
                label = (first.text_content() or "").strip()

                try:
                    if value:
                        select.select_option(value)
                    elif label:
                        select.select_option(label=label)
                    else:
                        # weird option - skip
                        continue
                except (PlaywrightError, AttributeError) as e:
                    logger.debug(
                        "ProductPage Failed to select option on a <select>: %s", e
                    )
                    continue

                logger.debug(
                    "ProductPage selected variation on <select>: value=%r, label=%r",value,label,
                )


            # Very generic selector for button-based variations
            variation_buttons = self.page.locator(
                "button[role='radio'], "
                "li[role='radio'] button, "
                "li[role='button'] button"
            )

            if variation_buttons.count() > 0:
                for i in range(variation_buttons.count()):
                    btn = variation_buttons.nth(i)
                    if not btn.is_visible():
                        continue

                    aria_pressed = btn.get_attribute("aria-pressed")
                    aria_checked = btn.get_attribute("aria-checked")

                    # skip buttons if already selected
                    if aria_pressed in ("true", "mixed") or aria_checked == "true":
                        continue

                    try:
                        btn.click()
                    except PlaywrightError as e:
                        logger.debug(
                            "ProductPage Failed to click variation button: %s", e
                        )
                        continue

                    logger.debug(
                        "ProductPage Auto-clicked variation button with text=%r",
                        (btn.text_content() or "").strip(),
                    )
                    break  # only one is needed

        except PlaywrightError as exc:
            # variation fail sould not make the test as awhole fail.
            logger.debug(
                "ProductPage Ignoring exception while trying to auto-select variations: %s",
                exc,
            )

# check if add to cart is a success or a failure (success on view of cart)
    def _wait_for_add_to_cart_confirmation(self, timeout: int = 8000) -> bool:

        try:
            # give the page time to react
            try:
                self.page.wait_for_load_state("networkidle", timeout=timeout)
            except PlaywrightTimeoutError:
                # continue to check forconfirmation anyway
                pass

            #success condition
            self.page.wait_for_selector(
                "a[href*='/cart'] >> text=View cart",
                timeout=timeout,
                state="visible",
            )
            logger.debug("View cart - confirmation detected.")
            return True

        except PlaywrightTimeoutError:
            # No cart confirmation - "This item cannot be added to your cart" or "Please select"

            error_locator = self.page.locator(
                "text=\"This item cannot be added to your cart\", "
                "text=\"Add to cart failed\", "
                "text=\"Please select\""
            )
            if error_locator.first.is_visible():
                logger.info("Add to cart appears to have failed (error message visible).")
            else:
                logger.info("No cart confirmation found - assuming add-to-cart failed.")
            return False

        except PlaywrightError as exc:
            # page or context closed while waiting
            logger.warning(
                "Page/context closed while waiting for add to cart confirmation: %s",
                exc,
            )
            return False

    def open(self, url:str):
        self.goto(url)
        # Wait for product title
        try:
            self.wait_for_visible("h1.it-ttl, h1.vi-atw-title")
        except PlaywrightError:
            # ignore if title is not found
            pass

# check if the page is appears loaded
    def is_loaded(self, timeout: int = 10_000):
        # wait for either a product title or add to cart button

        title_locator = self.page.locator(
            "h1[data-testid='x-item-title'], h1[itemprop='name']"
        ) # product title
        atc_locator = self.page.locator(
            "a:has-text('Add to cart'), button:has-text('Add to cart'), button[aria-label*='Add to cart']"
        )# add to cart button

        try:
            title_locator.first.wait_for(state="visible", timeout=timeout)
            #loaded
            return True
        except PlaywrightError:
            pass

        try:
            atc_locator.first.wait_for(state="visible", timeout=timeout)
            #loaded
            return True
        except PlaywrightError:
            pass

        return False

    def choose_default_variant(self) -> bool:
        # try <select> elements
        selects = self.page.locator(
            "select[name*='variant'], select[id*='msku-sel'], select[name*='size'], select[name*='color']"
        )
        if selects.count():
            sel = selects.first
            options = sel.locator("option:not([disabled])")
            if options.count() > 1:
                # pick first real option
                options.nth(1).click()
                return True
            elif options.count() == 1:
                options.first.click()
                return True

        # buttons / swatches / radio inputs
        variant_buttons = self.page.locator(
            "button[aria-label*='Select'], button[aria-label*='Color'], button[aria-label*='Size'], input[type='radio'], .msku-swatch--selectable"
        )
        if variant_buttons.count():
            for i in range(variant_buttons.count()):
                btn = variant_buttons.nth(i)
                try:
                    if btn.is_enabled() and btn.is_visible():
                        btn.click()
                        return True
                except (PlaywrightError, AttributeError):
                    continue

        # No variant found so assume no variant needed
        return True

    # trying to get the price and send it through my price parser
    def get_price(self):

        price_selectors = [
            "span#prcIsum",  # standard price
            "span#prcIsum_bidPrice",  # auction price
            "span#mm-saleDscPrc"  # sale price
        ]
        for selector in price_selectors:
            try:
                price_text = self.page.locator(selector).inner_text().strip()
                price_value = parse_price_to_number(price_text)
                if price_value > 0:
                    return price_value
            except (PlaywrightError, AttributeError, ValueError, TypeError):
                continue
        return 0.0

    # tries adding the product to cart, return bool
    def click_add_to_cart(self):
        # wait for page content to load
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
            self.page.wait_for_timeout(300)
        except PlaywrightError:
            print(f"Product page load state timeout: {self.page.url}")

        add_button_selectors = [
            "button#atcBtn_btn",
            "button#atcRedesignId_btn",
            "button:has-text('Add to cart')",
            "a:has-text('Add to cart')",
            "button[aria-label*='Add to cart']",
            "button[data-test-id='x-atc-action']",
        ]

        for selector in add_button_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.count() and btn.is_visible():
                    print(f"Clicking Add to Cart using selector: {selector}")
                    btn.click()
                    # wait for cart update or popups
                    try:
                        self.page.wait_for_load_state("networkidle", timeout=10_000)
                    except PlaywrightError:
                        #ignore -  still consider click as attempted
                        pass
                    return True
            except PlaywrightError as e:
                print(f"Selector '{selector}' failed: {e}")
                continue

        print(f"No Add to Cart button visible on product page: {self.page.url}")
        return False

# tries to handle all post add to cart click popups like warranty or things like that
    def handle_post_add_popups(self):

        popup_selectors = [
            "button#ADDON_0-cta",  # warranty upsell
            "button#addonSkipBtn",  # skip add‑on
            "button[aria-label='Close']",  # close icon
            "button:has-text('No thanks')",  # decline upsell
            "button:has-text('Continue shopping')",  # continue shopping
            "button:has-text('Go to cart')",  # proceed to cart
            "button:has-text('View cart')"  # view cart popup
        ]
        for selector in popup_selectors:
            try:
                btn = self.page.locator(selector)
                if btn.count() and btn.first.is_visible():
                    btn.first.click()
                    #wait for popup to close
                    self.page.wait_for_timeout(500)
                    break
            except PlaywrightError:
                continue

    # add to cart full sequence - url is provided: navigate to url
    #                           - url is None: assume already navigated to url
    #                           - return True if item confirmed as added to cart, False otherwise.
    def add_to_cart_full_seq(self, product_url: str | None = None):

        if product_url is None:
            # did not get a url – use current page
            product_url = self.page.url
            logger.debug(
                "add_to_cart_full_seq called without product_url, using current page: %s",
                product_url,
            )
        else:
            #navigate to the product page
            logger.debug("Opening product page: %s", product_url)
            self.page.goto(product_url, wait_until="networkidle")

        # select simple dropdown (if there is one)
        self._try_select_simple_variations()

        # try finding to cart button
        add_btn = self.page.locator(
            "a:has-text('Add to cart'), button:has-text('Add to cart')"
        ).first

        if not add_btn.is_visible():
            logger.warning(
                " No visible 'Add to cart' button for product: %s", product_url
            )
            return False

        logger.debug(
            "ProductPage found 'Add to cart' using selector: "
            "a/button:has-text('Add to cart')"
        )

        #click the button
        add_btn.click()
        logger.debug("Clicked Add to cart for: %s", product_url)

        # Wait for confirmation / error
        success = self._wait_for_add_to_cart_confirmation()

        if success:
            logger.info("Product added to cart (confirmed): %s", product_url)
        else:
            logger.warning(
                "Product NOT confirmed in cart (maybe needs size/color selection): %s",
                product_url,
            )

        return success

    #this is a bit duplicated but more robust function for clicking on add to cart
    #since eBay making it difficult for me
    def has_add_to_cart_button(self) -> bool:

        # common selectors on different eBay layouts
        candidate_selectors = [
            "button#atcRedesignId_btn",
            "a#isCartBtn_btn",
            "button#binBtn_btn",

            # Newer layouts
            "button[data-testid='x-atc-action']",
            "button[aria-label*='Add to cart']",
            "button[aria-label*='Add to Cart']",
            "a[aria-label*='Add to cart']",
            "a[aria-label*='Add to Cart']",

            #  CSS selectors text based
            "button:has-text('Add to cart')",
            "a:has-text('Add to cart')",
        ]
        for selector in candidate_selectors:
            try:
                some_locator = self.page.locator(selector).first
                # if there is no element
                if some_locator.count() == 0:
                    continue

                if some_locator.is_visible():
                    print(
                        f"ProductPage Found 'Add to cart' using selector: {selector}"
                    )
                    return True
            except PlaywrightError as e:
                # continue trying other selectors
                print(
                    f"ProductPage Selector {selector} raised {type(e).__name__}: {e}"
                )
                continue

        # fallback using role/text helpers
        try:
            btn = self.page.get_by_role("button", name="Add to cart")
            if btn.is_visible():
                print(
                    "ProductPage Found 'Add to cart' via get_by_role(button, 'Add to cart')."
                )
                return True
        except PlaywrightError:
            pass

        try:
            btn_text = self.page.get_by_text("Add to cart", exact=False)
            if btn_text.is_visible():
                print(
                    "ProductPage Found 'Add to cart' via get_by_text('Add to cart')."
                )
                return True
        except PlaywrightError:
            pass

        return False

class CartPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

    def is_loaded(self):
        try:
            self.wait_for_visible("#Cart"),
            return True
        except PlaywrightError:
            return False

    def open(self):

        self.goto("https://cart.ebay.com/")
        self.is_loaded()

    def get_cart_item_rows(self):
        # return a list of elements for eaxh item row in the cart
        rows = self.page.locator("div.cart-bucket")
        return rows.element_handles()

    def get_cart_item_titles(self):
        # return the titles of all items in the cart as a list
        #the titles are stored inside the utem row. iterate on the rows and get the text.
        titles = []
        for row in self.get_cart_item_rows():
            try:
                title = row.query_selector("a.item-title").inner_text().strip()
                titles.append(title)
            except (PlaywrightError, AttributeError):
                continue
        return titles

    # return a list of prices per item. each row contains proce element.
    # then we pass the price through price parser. if a price cannot be parsed - ignore it.
    def get_cart_item_prices(self):
        prices = []
        for row in self.get_cart_item_rows():
            try:
                price_text = row.query_selector("span.item-price").inner_text().strip()
                price_value = parse_price_to_number(price_text)
                prices.append(price_value)
            except (PlaywrightError, AttributeError, ValueError, TypeError):
                continue

        return prices

    # return the total car price. if no total can be found return 0.0
    # if total found parse it  with our price parser
    def get_cart_total(self):

        total_price_selectors = [
            "span#SUBTOTAL",  # sometimes used
            "span#total",  # fallback
            "div#SUBTOTAL div"  # older markup
        ]
        for selector in total_price_selectors:
            try:
                elem = self.page.locator(selector)
                if elem.is_visible():
                    text = elem.inner_text().strip()
                    return parse_price_to_number(text)
            except (PlaywrightError, AttributeError, ValueError, TypeError):
                continue
        #fallback - sum individual prices
        return sum(self.get_cart_item_prices())

    # return True if cart is empty, otherwise False.
    # check for "you dont have any items in your cart" message
    def is_cart_empty(self):
        try:
            empty_msg = self.page.locator("#Cart .empty-cart__title")
            return empty_msg.is_visible()
        except PlaywrightError:
            return False

