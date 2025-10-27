from ollama import chat
from ollama import ChatResponse

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
    

if __name__ == "__main__":
    model = "gemma3:1b"
    prompt = "Explain the theory of relativity in simple terms."
    print("Synchronous response:")
    print(getResponse(prompt, model))


