import requests
import json

def chat_with_ollama(prompt, model="qwen2.5:7b"):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("🤖 JuniorGPT - Your Personal AI Assistant")
    print("Type 'quit' to exit")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        print("AI: ", end="", flush=True)
        response = chat_with_ollama(user_input)
        print(response)

if __name__ == "__main__":
    main()
