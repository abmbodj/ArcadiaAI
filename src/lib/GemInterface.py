import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from typing import Any, Optional


class AiInterface:
    """
    Keeps the original synchronous web scraper (requests + BeautifulSoup) but improves it
    by adding a requests.Session with browser-like headers and a retry strategy to reduce
    403/429/5xx failures. Everything else remains async-friendly by running blocking
    operations in a threadpool.

    Usage:
      ai = AiInterface()
      result = asyncio.run(ai.Archie("When is fall break?"))
    """

    def __init__(
            
        self,
        debug: bool = False,
        scraper_max_retries: int = 3,
        scraper_backoff_factor: float = 1.0,
        scraper_timeout: int = 15,
    ):
        
            
        # Load the variables from the .env file into the environment
        load_dotenv()

        # Retrieve the API key from the environment
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Check if the key was found
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Check your .env file or environment.")

        # Initialize the Client object (synchronous genai client)
        self.client = genai.Client(api_key=self.api_key)

        # Debug flag
        self.debug = debug

        # Scraper configuration
        self.scraper_timeout = scraper_timeout

        # Create a requests.Session with headers and retry strategy
        self.session: requests.Session = requests.Session()
        # Browser-like default headers to reduce likelihood of 403 from simple bot checks
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            # requests will automatically handle gzip/deflate; no need to set Accept-Encoding typically
        })

        # Configure retries for transient errors and common rate-limit statuses.
        retry_strategy = Retry(
            total=scraper_max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=scraper_backoff_factor,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _log(self, *args):
        if self.debug:
            print("[AiInterface DEBUG]", *args)

    def generate_text(self, prompt: str) -> str:
        """
        Synchronous compatibility method retained: generate text using the genai client.
        This method behaves like the original code if called synchronously.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return response.text
        except APIError as e:
            return f"An API Error occurred during text generation: {e}"

    def scrape_website(self, url: str, timeout: Optional[int] = None) -> str:
        """
        Improved synchronous web scraper that:
        - uses a persistent requests.Session with browser-like headers
        - has a Retry strategy for transient status codes (429, 5xx)
        - keeps the interface synchronous (requests + BeautifulSoup) as requested
        """
        try:
            to = timeout if timeout is not None else self.scraper_timeout
            self._log(f"Scraping {url} with timeout={to}")
            response = self.session.get(url, timeout=to, allow_redirects=True)
            # If raise_for_status raises, we catch below and return a helpful message
            try:
                response.raise_for_status()
            except requests.HTTPError as http_err:
                # Provide helpful debug string but still try to return body if available
                self._log(f"HTTP error for {url}: {http_err} (status {response.status_code})")
                # If server returned some HTML (e.g., Cloudflare block), parse and return its text
                # Otherwise, return the error string
                if response.text:
                    soup = BeautifulSoup(response.text, "html.parser")
                    return soup.get_text()
                return f"HTTP error when scraping {url}: {http_err}"

            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            self._log(f"RequestException when scraping {url}: {e}")
            return f"An error occurred while scraping the website: {e}"
        except Exception as e:
            self._log(f"Unexpected error when scraping {url}: {e}")
            return f"An unexpected error occurred while scraping the website: {e}"


    async def generate_text_async(self, prompt: str) -> str:
        """
        Async wrapper around the synchronous genai client call.
        Runs the synchronous operation in a threadpool to avoid blocking the event loop.
        """
        def _sync_generate() -> str:
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt
                )
                return getattr(response, "text", str(response))
            except APIError as e:
                return f"An API Error occurred during text generation: {e}"
            except Exception as e:
                return f"Unexpected error during text generation: {e}"

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_generate)

    async def _run_in_executor(self, func: Any, *args, **kwargs):
        """
        Helper to run any synchronous function in the default threadpool and return its result.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def Archie(self, query: str) -> str:

        """
        Async entry point that:
        - Executes the original synchronous scrape_website concurrently in threads
        so the async event loop is not blocked.
        - Uses the async generate_text_async wrapper to call the Gemini client
        without blocking the event loop.
        """
        urls = {
            "website": "https://www.arcadia.edu/",
            "events": "https://www.arcadia.edu/events/?mode=month",
            "about": "https://www.arcadia.edu/about-arcadia/",
            "weather": "https://weather.com/weather/today/l/b0f4fc1167769407f55347d55f492a46e194ccaed63281d2fa3db2e515020994",
            "diningHours": "https://www.arcadia.edu/life-arcadia/living-commuting/dining/",
            "ITresources": "https://www.arcadia.edu/life-arcadia/campus-life-resources/information-technology/",
        }

        # Launch all scraping calls concurrently in the threadpool (so we keep the sync scraper unchanged)
        scrape_tasks = {
            name: asyncio.create_task(self._run_in_executor(self.scrape_website, url))
            for name, url in urls.items()
        }

        # Wait for all scrapes to finish
        results = {}
        for name, task in scrape_tasks.items():
            try:
                print(f"Waiting for scrape task: {name}")
                results[name] = await task
            except Exception as e:
                # Shouldn't happen often, but catch to ensure Archie continues gracefully
                results[name] = f"Error during scraping {name}: {e}"

        prompt = f"""System: You are ArchieAI an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university. You were made by Eva Akselrad and Ab.
Using the following website content, answer the query: {query}

Website Content:
{results.get('website', '')}

Events Content:
{results.get('events', '')}

About Content:
{results.get('about', '')}

Weather Content:
{results.get('weather', '')}

Dining Hours Content:
{results.get('diningHours', '')}

IT Resources Content:
{results.get('ITresources', '')}
"""
        # Call the genai client without blocking the event loop
        print("Generating text with prompt:", prompt)
        return await self.generate_text_async(prompt)
    
    

if __name__ == "__main__":
    # Simple test of the AiInterface
    ai = AiInterface(debug=True)
    test_query = "When is fall break?"
    response = asyncio.run(ai.Archie(test_query))
    print("Response to query:", test_query)
    print(response)