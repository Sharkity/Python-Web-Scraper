from bs4 import BeautifulSoup
import requests
import time
from datetime import date
from typing import Optional
import subprocess

# Optional TTS engine (pyttsx3); fallback to macOS 'say' if unavailable
try:
    import pyttsx3  # type: ignore
    _tts_engine = pyttsx3.init()
except Exception:
    _tts_engine = None


def speak(text: Optional[str]) -> None:
    """Speak text aloud if possible, otherwise no-op.

    Tries pyttsx3 first (offline, cross-platform). If unavailable or failing,
    falls back to macOS 'say' command.
    """
    if not text:
        return
    # Try pyttsx3
    if _tts_engine is not None:
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
            return
        except Exception:
            pass
    # Fallback to macOS say
    try:
        subprocess.run(["say", text], check=False)
    except Exception:
        pass

retries = 5

# Always use the base URL built from today's date
today = date.today()
url = f"https://wol.jw.org/en/wol/h/r1/lp-e/{today.year}/{today.month}/{today.day}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19042",
    "Accept-Language": "en-US, en;q=0.5",
}

# Helper: extract both the theme scripture (p.themeScrp) and the daily text (p.sb)
# for the target day by matching the parent tabContent[data-date]
from typing import Tuple

def extract_day_text(html: bytes, target: date) -> Tuple[Optional[str], Optional[str]]:
    soup = BeautifulSoup(html, "html.parser")

    # The page groups each day in a div.tabContent with an ISO UTC data-date at midnights
    target_attr = f"{target.isoformat()}T00:00:00.000Z"
    container = soup.select_one(f'div.tabContent[data-date="{target_attr}"]')

    if not container:
        # Fallback: locate the day's h2, then read nearby p.themeScrp and p.sb
        import calendar
        month_name = calendar.month_name[target.month]
        day_text = f"{month_name} {target.day}"
        h2 = None
        for node in soup.select("h2[id][data-pid]"):
            if day_text in node.get_text(" ", strip=True):
                h2 = node
                break
        if h2:
            theme = h2.find_next_sibling("p", class_="themeScrp")
            sb = h2.find_next_sibling("p", class_="sb")
            return (
                theme.get_text(strip=True) if theme else None,
                sb.get_text(strip=True) if sb else None,
            )
        return (None, None)

    # Within the correct day's container, select theme scripture and daily text
    theme = container.select_one("p.themeScrp")
    sb = container.select_one("p.sb")
    return (
        theme.get_text(strip=True) if theme else None,
        sb.get_text(strip=True) if sb else None,
    )

for attempt in range(1, retries + 1):
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            theme_text, daily_text = extract_day_text(resp.content, today)
            if theme_text:
                print(theme_text)
                speak(theme_text)
            else:
                msg = "No theme scripture found for today on this page."
                print(msg)
                speak(msg)

            if daily_text:
                print(daily_text)
                speak(daily_text)
            else:
                msg = "No daily text found for today on this page."
                print(msg)
                speak(msg)
            break
        else:
            msg = f"HTTP {resp.status_code}: {resp.reason}"
            print(msg)
            speak(msg)
    except requests.RequestException as e:
        msg = f"An error occurred: {e}"
        print(msg)
        speak(msg)

    if attempt < retries:
        wait = 2 * attempt  # simple linear backoff
        retry_msg = f"Retrying in {wait}s... ({retries - attempt} attempts left)"
        print(retry_msg)
        speak(retry_msg)
        time.sleep(wait)
