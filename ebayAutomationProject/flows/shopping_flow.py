from pathlib import Path
from pages.shop_pages import LoginPage, SearchResultsPage, ProductPage, CartPage, HomePage
from utils import price_parser

def login(page, username:str, password:str):

    login_page = LoginPage(page)
    #return boolean result of page object
    return login_page.login_full_seq(username, password)

def search_items_by_name_under_price(page, query:str, max_price:float, limit:int):
    home_page = HomePage(page)
    result_page = HomePage.search_for(query)

    # wait for results and use the orice filter
    result_page.is_loaded()
    result_page.apply_max_price_filter(max_price)

    item_urls = result_page.collect_items_under_price_accross_pages(max_price, limit)
    print(f"Query '{query}' – requested limit={limit}, max_price={max_price}")
    print(f"Collected {len(item_urls)} item URLs")
    return item_urls

def add_items_to_cart(page, item_urls:list[str]):

    product_page = ProductPage(page)
    if not item_urls:
        print("add_items_to_cart has been called with an empty list")
        return

    photos_dir = Path("photos")
    photos_dir.mkdir(exist_ok=True)

    total = len(item_urls)

    for index, url in enumerate(item_urls, start=1):
        print(f"openning product {index}/{total}")
        product_page.open(url)

        try:
            existing = len(list(photos_dir.glob("product_*.png")))
            screenshot_path = photos_dir / f"{existing +1}.png"

            try:
                page.screenshot(path= str(screenshot_path),full_page=True)

            except Exception:
                #fallback
                page.screenshot(path=str(screenshot_path))

            print(f"saved screenshot: {screenshot_path}")
        except Exception as e:
            print(f"could't save screenshot for product: {index}:{e}")

        # make sure the page is fully loaded
        if not product_page.is_loaded():
            print(f"Product page {index}/{total} did not fully load")
        # add to cart
        if product_page.has_add_to_cart_button():
            print(f"Add to Cart button FOUND for product {index} – clicking it")
            try:
                product_page.add_to_cart_full_seq()
                print(f"Finished add_to_cart_full_seq for product {index}")
            except Exception as e:
                print(f"Exception while adding to cart for product {index}: {e}")
        else:
            print(f"no add to cart button visible for product {index}")

def assert_cart_total_not_exceeds_limit(page, max_total:float):
    cart_page = CartPage(page)
    cart_page.open()
    total = cart_page.get_cart_total()
    assert total <= max_total, f"Cart total {total} exceeds maximum allowed {max_total}"