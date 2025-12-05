
# convert price string to a float, keeping only digits or decimal points.
def parse_price_to_number(price_text: str):

    # validate input
    if not isinstance(price_text, str) or not price_text.strip():
        return 0.0

    price = price_text.strip()

    # remove known prefixes
    currency_prefixes = ("US", "EUR", "GBP", "ILS", "From", "Approximately", "about")
    for prefix in currency_prefixes:
        if price.startswith(prefix):
            price = price[len(prefix):].strip()
            break

    # keep only digits, commas and periods
    numeric_chars = []
    for char in price:
        if char.isdigit() or char in {",", "."}:
            numeric_chars.append(char)

    cleaned_price = "".join(numeric_chars)

    # if there is exactly one comma and no dot -  treat comma as a decimal
    if cleaned_price.count(",") == 1 and cleaned_price.count(".") == 0:
        cleaned_price = cleaned_price.replace(",", ".")

    # remove all commas
    cleaned_price = cleaned_price.replace(",", "")

    # convert to float
    try:
        return float(cleaned_price)
    except ValueError:
        return 0.0
