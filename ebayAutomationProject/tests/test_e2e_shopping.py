
from utils.data_loader import load_test_scenarios, load_user_credentials
from flows.shopping_flow import login, search_items_by_name_under_price, add_items_to_cart, assert_cart_total_not_exceeds_limit
import shutil
from pathlib import Path

def test_e2e_add_items_and_verify_total(page):

    # try removing any screenshots left from priviuos run
    photos_dir = Path("photos")
    if photos_dir.exists():
        try:
            shutil.rmtree(photos_dir)
        except Exception:
            # if the directory cannot be removed continue.
            pass
    #make a new one
    photos_dir.mkdir(parents=True, exist_ok=True)

    # load scenarios and user credentials
    scenarios = load_test_scenarios()
    users = load_user_credentials()

    for scenario in scenarios:
        query = scenario["query"]
        max_price = scenario["maxPrice"]
        limit = scenario.get("limit", 5)
        max_cart_total = scenario["maxCartTotal"]
        user_key = scenario.get("userKey", "defaultUser")
        creds = users[user_key]
        # perform login
        logged_in = login(page, creds["username"], creds["password"])
        assert logged_in, f"Login failed for user {user_key}"
        # search for items and collect urls
        item_urls = search_items_by_name_under_price(page, query, max_price, limit)
        # add items to cart
        add_items_to_cart(page, item_urls)
        # verify cart total
        assert_cart_total_not_exceeds_limit(page, max_cart_total)