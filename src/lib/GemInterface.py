import os
import asyncio
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from typing import Any, Optional, AsyncIterator
import json

from ollama import chat, AsyncClient
from ollama import ChatResponse

class AiInterface:
    """
    AI Interface using Ollama for local LLM inference with streaming support.
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

        # Retrieve the model name from environment (defaults to llama2 if not set)
        self.model = os.getenv("MODEL", "llama2")
        
        # Initialize Ollama async client for streaming
        self.async_client = AsyncClient()

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

    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """
        Synchronous method: generate text using Ollama client.
        This method is kept for backwards compatibility.
        """
        try:
            messages = []
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt,
                })
            messages.append({
                'role': 'user',
                'content': prompt,
            })
            
            response: ChatResponse = chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            self._log(f"Error during text generation: {e}")
            return "An error occurred during text generation"

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
            return "An error occurred while scraping the website"
        except Exception as e:
            self._log(f"Unexpected error when scraping {url}: {e}")
            return "An unexpected error occurred while scraping the website"


    async def generate_text_async(self, prompt: str, system_prompt: str = "") -> str:
        """
        Async wrapper around Ollama chat for non-streaming responses.
        Runs the operation in a threadpool to avoid blocking the event loop.
        """
        def _generate_text(prompt: str, system_prompt: str = "") -> str:
            messages = []
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt,
                })
            messages.append({
                'role': 'user',
                'content': prompt,
            })
            
            try:
                response: ChatResponse = chat(model=self.model, messages=messages)
                return response['message']['content']
            except Exception as e:
                self._log(f"Error during text generation: {e}")
                return "An error occurred during text generation"
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _generate_text, prompt, system_prompt)
    
    async def generate_text_streaming(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """
        Async streaming generator that yields tokens as they are generated by Ollama.
        This allows for real-time display of the AI's thinking process.
        
        Usage:
            async for token in ai.generate_text_streaming(prompt, system):
                print(token, end='', flush=True)
        """
        messages = []
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt,
            })
        messages.append({
            'role': 'user',
            'content': prompt,
        })
        
        try:
            stream = await self.async_client.chat(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except Exception as e:
            with open("error.txt", "w", encoding="utf-8") as f:
                f.write(str(e))
            yield "An error occurred during streaming"

    async def _run_in_executor(self, func: Any, *args, **kwargs):
        """
        Helper to run any synchronous function in the default threadpool and return its result.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def Archie(self, query: str) -> str:
        """
        Main async entry point for the Archie AI assistant.
        Uses scraped data from JSON file to provide context for answering queries.
        """
        with open("data/scrape_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        
        system_prompt = f"""You are ArchieAI, an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university.

You are made by students for a final project. You must be factual and accurate based on the information provided. It is ok to say "I don't know" if you are unsure.

Respond based on your knowledge up to 2025.

Use the following content to better answer the query:
{json.dumps(results, indent=2)}"""

        return await self.generate_text_async(query, system_prompt=system_prompt)
    
    async def Archie_streaming(self, query: str) -> AsyncIterator[str]:
        """
        Streaming version of Archie that yields tokens as they are generated.
        This provides a better user experience by showing the AI "thinking" in real-time.
        
        Usage:
            async for token in ai.Archie_streaming("When is fall break?"):
                print(token, end='', flush=True)
        """
        with open("data/scrape_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        
        system_prompt = f"""You are ArchieAI, an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university.

You are made by students for a final project. You must be factual and accurate based on the information provided. It is ok to say "I don't know" if you are unsure.

Respond based on your knowledge up to 2025.

Use the following content to better answer the query:
{json.dumps(results, indent=2)}"""

        async for token in self.generate_text_streaming(query, system_prompt=system_prompt):
            yield token
    

if __name__ == "__main__":
    # Simple test of the AiInterface
    ai = AiInterface(debug=True)
    test_query = "When is fall break?"
    response = asyncio.run(ai.Archie(test_query))
    print("Response to query:", test_query)
    print(response)
