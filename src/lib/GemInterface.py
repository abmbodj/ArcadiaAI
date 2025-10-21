import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
import requests
from bs4 import BeautifulSoup

class AiInterface:
    def __init__(self):
        # Load the variables from the .env file into the environment
        load_dotenv()

        # Retrieve the API key from the environment
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Check if the key was found
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Check your .env file or environment.")

        # Initialize the Client object
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, prompt: str) -> str:
        """
        Generate text based on the given prompt using a Gemini model via the Client.
        """
        try:
            # Call generate_content on the client's models service
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return response.text
        except APIError as e:
            return f"An API Error occurred during text generation: {e}"

    def scrape_website(self, url: str) -> str:
        """
        Scrape the content of a given website and return it as a string.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP issues
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            return f"An error occurred while scraping the website: {e}"

    def arcadia_gen(self, query: str) -> str:
        """
        Generate a response for a query using Arcadia University website content.
        """
        website = self.scrape_website("https://www.arcadia.edu/")
        events = self.scrape_website("https://www.arcadia.edu/events/?mode=month")
        about = self.scrape_website("https://www.arcadia.edu/about-arcadia/")

        prompt = f"""System: You are ArchieAI an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university. You were made by Eva Akselrad and Ab.
        Using the following website content, answer the query: {query}\n\nWebsite Content:\n{website}\n\nEvents Content:\n{events}\n\nAbout Content:\n{about}"""
        return self.generate_text(prompt)
