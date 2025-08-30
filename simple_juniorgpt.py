import gradio as gr
import requests
import json

def call_ollama(prompt, model="qwen2.5:7b"):
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
        return f"Error connecting to Ollama: {str(e)}"

def chat_with_ai(message, history, model_choice):
    if not message.strip():
        return history, ""
    
    response = call_ollama(message, model_choice)
    history.append((message, response))
    return history, ""

def get_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        else:
            return ["qwen2.5:7b"]
    except:
        return ["qwen2.5:7b"]

# Create interface
with gr.Blocks(title="JuniorGPT") as demo:
    gr.Markdown("# 🤖 JuniorGPT - Your Personal AI Assistant")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(label="Your message", placeholder="Ask me anything...")
            send_btn = gr.Button("Send")
            clear_btn = gr.Button("Clear")
        
        with gr.Column(scale=1):
            model_dropdown = gr.Dropdown(
                choices=get_models(),
                value="qwen2.5:7b",
                label="AI Model"
            )
    
    send_btn.click(chat_with_ai, [msg, chatbot, model_dropdown], [chatbot, msg])
    msg.submit(chat_with_ai, [msg, chatbot, model_dropdown], [chatbot, msg])
    clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

if __name__ == "__main__":
    demo.launch(share=True)
