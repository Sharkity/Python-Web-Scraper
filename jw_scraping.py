from bs4 import BeautifulSoup
import requests
import time
from datetime import date
from typing import Optional

retries = 5

# Always use the base URL built from today's date
today = date.today()
url = f"https://wol.jw.org/en/wol/h/r1/lp-e/{today.year}/{today.month}/{today.day}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19042",
    "Accept-Language": "en-US, en;q=0.5",
}

# Helper: extract the specific p.sb for the target day by matching the parent tabContent[data-date]
def extract_day_text(html: bytes, target: date) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")

    # The page groups each day in a div.tabContent with an ISO UTC data-date at midnight
    target_attr = f"{target.isoformat()}T00:00:00.000Z"
    container = soup.select_one(f'div.tabContent[data-date="{target_attr}"]')

    if not container:
        # Fallback: if container not found, try picking the h2 that contains the human date and then the next p.sb
        # Example h2 text: "Wednesday, August 13"
        # Build expected pieces to reduce false matches
        import calendar
        month_name = calendar.month_name[target.month]
        day_text = f"{month_name} {target.day}"
        h2 = None
        for node in soup.select("h2[id][data-pid]"):
            if day_text in node.get_text(" ", strip=True):
                h2 = node
                break
        if h2:
            # Find the first following sibling p.sb
            sib = h2.find_next_sibling("p", class_="sb")
            if sib:
                return sib.get_text(strip=True)
        return None

    # Within the correct day's container, select the first p with class sb
    p = container.select_one("p.sb")
    return p.get_text(strip=True) if p else None

for attempt in range(1, retries + 1):
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            text = extract_day_text(resp.content, today)
            if text:
                print(text)
            else:
                print("No daily text found for today on this page.")
            break
        else:
            print(f"HTTP {resp.status_code}: {resp.reason}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

    if attempt < retries:
        wait = 2 * attempt  # simple linear backoff
        print(f"Retrying in {wait}s... ({retries - attempt} attempts left)")
        time.sleep(wait)
