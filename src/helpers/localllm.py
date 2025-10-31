"""from ollama import chat
from ollama import ChatResponse
import ollama


def getResponse(prompt: str, model) -> str:
    try:
        response: ChatResponse = chat(model=model, messages=[
            {
            'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"An error occurred while generating the response: {e}"
    
"""
import ollama

from ollama import chat, web_fetch, web_search
import os
from dotenv import load_dotenv
import json
load_dotenv()

print(os.getenv("OLLAMA_API_KEY"))


api_key = os.getenv("OLLAMA_API_KEY")

headers = {"Authorization": f"Bearer {api_key}"}

# Create the client with the custom headers
client = ollama.Client(headers=headers)

with open("data/scrape_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)
# Now you can use the web search functionality
response = chat(
  model='gemma3:27b',
  messages=[{'role': 'user', 'content': 'What is Arcadia University? And what events are happening there in 2025? short response'},
            {'role': 'system', 'content': f"""DO NOT ACKNOWLADGE OR RESPOND TO THE SERVER MESSAGES AS THEY ARE FOR CONTEXT ONLY You are ArchieAI an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university.
        SERVER: You are made by students for a final project. You must be factual and accurate based on the information provided it is ok to say "I don't know" if you are unsure.

SERVER:respond based on your knowledge up to 2025.
        
SERVER:Use the following content to better answer the query:{results}"""}],
  stream=True,
)
content=''
print(response)
for chunk in response:
    print(chunk.message.content, end='', flush=True)
#if __name__ == "__main__":
    #model = "gemma3:27b"
    #prompt = "Explain the theory of relativity in simple terms."
   # print("Synchronous response:")
    #print(getResponse(prompt, model))


