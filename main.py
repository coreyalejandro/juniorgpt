import gradio as gr
import sqlite3
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
import os

class JuniorGPTAffordable:
    def __init__(self):
        self.setup_database()
        self.setup_logging()
        self.ollama_url = "http://localhost:11434"
        
    def setup_database(self):
        """Initialize SQLite database for conversations"""
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect('data/conversations.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_input TEXT,
                agent_response TEXT,
                model_used TEXT,
                response_time REAL
            )
        ''')
        conn.commit()
        conn.close()
        
    def setup_logging(self):
        """Configure logging system"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/juniorgpt.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def call_ollama(self, prompt: str, model: str = "qwen2.5:7b") -> str:
        """Call Ollama API to get response"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
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
            self.logger.error(f"Ollama API error: {e}")
            return f"Error connecting to Ollama: {str(e)}"
        
    def process_user_input(self, user_input: str, chat_history: List, model_choice: str) -> tuple:
        """Main processing function for user input"""
        if not user_input.strip():
            return chat_history, ""
            
        try:
            start_time = datetime.now()
            
            # Get response from Ollama
            response = self.call_ollama(user_input, model_choice)
            
            # Update chat history
            chat_history.append([user_input, response])
            
            return chat_history, ""
            
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            error_response = f"Error: {str(e)}"
            chat_history.append([user_input, error_response])
            return chat_history, ""
            
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            else:
                return ["qwen2.5:7b"]
        except:
            return ["qwen2.5:7b"]
        
    def create_interface(self):
        """Create Gradio interface"""
        available_models = self.get_available_models()
        
        with gr.Blocks(title="JuniorGPT - Affordable AI Assistant") as interface:
            gr.Markdown("# 🤖 JuniorGPT - Your Personal AI Assistant")
            gr.Markdown("Powered by local AI models via Ollama")
            
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=400,
                        show_label=True
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            label="Your message",
                            placeholder="Ask me anything...",
                            lines=2,
                            scale=3
                        )
                        
                        model_choice = gr.Dropdown(
                            choices=available_models,
                            value=available_models[0] if available_models else "qwen2.5:7b",
                            label="AI Model",
                            scale=1
                        )
                    
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear Chat")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### System Status")
                    status_display = gr.JSON(
                        label="System Info",
                        value={"status": "Ready", "models": len(available_models)}
                    )
            
            # Event handlers
            submit_btn.click(
                fn=self.process_user_input,
                inputs=[user_input, chatbot, model_choice],
                outputs=[chatbot, user_input]
            )
            
            user_input.submit(
                fn=self.process_user_input,
                inputs=[user_input, chatbot, model_choice],
                outputs=[chatbot, user_input]
            )
            
            clear_btn.click(
                fn=lambda: ([], ""),
                outputs=[chatbot, user_input]
            )
            
        return interface

# Launch application
if __name__ == "__main__":
    app = JuniorGPTAffordable()
    interface = app.create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False
    )
