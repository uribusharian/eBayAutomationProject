README – eBay End-to-End Shopping Test
============================

Overview
--------
This project is an end-to-end (E2E) UI test framework for eBay using:

- Python
- Playwright (via pytest)
- Data-driven tests (JSON files)

The main scenario:

1. Log in to eBay with a test user.
2. For each test scenario (search term + max price):
   - Search the site.
   - Collect a limited number of products under a max price.
   - Open each product page, take a screenshot, and try to add it to the cart.
3. Open the cart and verify the total does not exceed a calculated budget.
4. Save an HTML report and screenshots for inspection.


1. Prerequisites
----------------

1. Python  
   - Python 3.10+ (you are currently using 3.13, which is fine).

2. An eBay test account  


2. Install & Environment Setup
------------------------------

From the project root:

1. (Optional but recommended) Create and activate a virtual environment:

   Windows (PowerShell):
   - python -m venv .venv
   - .venv\Scripts\Activate.ps1

2. Install Python dependencies:

   pip install -r requirements.txt

   If you do not have a requirements file yet, at minimum you need:

   pip install pytest playwright pytest-playwright pytest-html

3. Install Playwright browsers:

   playwright install


3. User Preparation
-------------------

Create a test account on eBay and log in manually once.

1. Add a **default shipping address**  
   This prevents eBay from showing an address setup popup that breaks automation.

2. Optional: Add non-real payment info  
   Not required for adding items to the cart.

3. Test login manually in a normal browser to ensure:
   - No “complete registration” popups appear
   - No forced address verification
   - No account restrictions


4. CAPTCHA / Human Verification
-------------------------------

eBay often triggers CAPTCHA when detecting automation.

The test **does NOT bypass CAPTCHA**.

Explanation:

- during login you MUST manually solve the CAPTCHA.
- Run tests in **headed mode** (browser visible) so you can complete it.

Command:

pytest --headed -s

When login starts:
- Watch the opened browser window
- Solve the CAPTCHA / “I’m not a robot”
- The automation will continue automatically after you click “Continue”


5. Configuring users.json
-------------------------

The test reads user credentials from:

data/users.json

Example:

{
  "defaultUser": {
    "username": "your-email@example.com",
    "password": "your-ebay-password"
  }
}

Replace the values with your real test user.


6. Configuring test_scenarios.json
----------------------------------

This file defines what products to search and test.

Example:

[
  {
    "name": "Running shoes under 300",
    "query": "running shoes",
    "maxPrice": 300,
    "limit": 5,
    "budgetPerItem": 300,
    "userKey": "defaultUser"
  }
]


7. Running the Test
-------------------

From the project root:

pytest --headed --html=reports/report.html --self-contained-html

After the run:

- Screenshots saved to: photos/
- HTML report saved to: reports/report.html


8. Troubleshooting
------------------

Login stuck:
- Solve CAPTCHA
- Make sure password is correct
- Check if eBay is asking for address verification

Cart shows fewer items:
- Item requires a variation not auto-selected
- Add-to-cart button hidden or changed by seller

Playwright errors:
- Run: playwright install


End of README
