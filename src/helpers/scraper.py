import os
import json
import asyncio
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from typing import Optional


def scrape_website(url: str, timeout: Optional[int] = None) -> str:
    """
    Improved synchronous web scraper that:
    - creates a requests.Session with browser-like headers
    - has a Retry strategy for transient status codes (429, 5xx)
    - keeps the interface synchronous (requests + BeautifulSoup)
    """
    # build a session with a retry strategy
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    session.headers.update(headers)

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    to = timeout if timeout is not None else 10  # default timeout in seconds
    print(f"Scraping {url} with timeout={to}")
    try:
        response = session.get(url, timeout=to, allow_redirects=True)
        try:
            response.raise_for_status()
        except requests.HTTPError as http_err:
            # provide helpful debug string but still return any HTML body if present
            print(f"HTTP error for {url}: {http_err} (status {getattr(response, 'status_code', 'unknown')})")
            if response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                return soup.get_text()
            return f"HTTP error when scraping {url}: {http_err}"

        # successful response
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except requests.RequestException as e:
        print(f"RequestException when scraping {url}: {e}")
        return f"An error occurred while scraping the website: {e}"
    except Exception as e:
        print(f"Unexpected error when scraping {url}: {e}")
        return f"An unexpected error occurred while scraping the website: {e}"

def background_checker():
    urls = {
        "website": "https://www.arcadia.edu/",
        "events": "https://www.arcadia.edu/events/?mode=month",
        "about": "https://www.arcadia.edu/about-arcadia/",
        "weather": "https://weather.com/weather/today/l/b0f4fc1167769407f55347d55f492a46e194ccaed63281d2fa3db2e515020994",
        "diningHours": "https://www.arcadia.edu/life-arcadia/living-commuting/dining/",
        "ITresources": "https://www.arcadia.edu/life-arcadia/campus-life-resources/information-technology/",
        "Academic Calendar": "https://www.arcadia.edu/academics/resources/academic-calendars/2025-26/",
    }

    dictionary = {}
    for name, url in urls.items():
        #sanitize result by removing newlines and excessive whitespace
        result = scrape_website(url=url)
        result = ' '.join(result.split())
        dictionary[name] = result

    # ensure the data directory exists, then write the collected dictionary as JSON
    os.makedirs(os.path.dirname("data/scrape_results.json"), exist_ok=True)
    #sanitize the data i.e removing /n and \n and other chars like that
    with open("data/scrape_results.json", "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=4)
import time
if __name__ == "__main__":
    while True:
        print("Scraping websites and saving results...")
        background_checker()
        print("Scraping completed and results saved to data/scrape_results.json")
        time.sleep(3600)