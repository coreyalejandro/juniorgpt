"""
JuniorGPT - Secure Multi-Agent AI Assistant
Enhanced version with modular architecture and security improvements
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
import logging
import uuid
import time
from datetime import datetime

# Flask and web components
from flask import Flask, render_template_string, request, jsonify, Response, session
from flask import stream_template
from markupsafe import Markup

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from config import Config, get_config
from models import init_db, Conversation, Agent
from services import AgentService, ModelService, ConversationService
from utils.security import SecurityUtils
from utils.logging_config import setup_logging, get_logger

# Initialize configuration
config = get_config()

# Validate configuration
if not config.validate():
    print("Configuration validation failed. Please check your environment variables.")
    sys.exit(1)

# Setup logging
logger = setup_logging(
    log_level=config.LOG_LEVEL,
    log_file=config.LOG_FILE,
    include_console=True
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize database
try:
    db = init_db(config.DATABASE_URL, config.DATABASE_ECHO)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    sys.exit(1)

# Initialize services
try:
    model_service = ModelService(config)
    agent_service = AgentService(model_service)
    conversation_service = ConversationService()
    security = SecurityUtils()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    sys.exit(1)

# Global state for conversations
active_conversations = {}

# HTML Template with security improvements
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token }}">
    <title>JuniorGPT - Secure AI Assistant</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --success-color: #10b981;
            --danger-color: #ef4444;
            --warning-color: #f59e0b;
            --bg-color: #f8fafc;
            --surface-color: #ffffff;
            --text-color: #1e293b;
            --border-color: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: var(--surface-color);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: var(--primary-color);
            margin-bottom: 10px;
        }
        
        .header p {
            color: var(--secondary-color);
            margin: 0;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
            flex: 1;
        }
        
        .chat-container {
            background: var(--surface-color);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: 600px;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            max-width: 80%;
        }
        
        .message.user {
            background: var(--primary-color);
            color: white;
            margin-left: auto;
        }
        
        .message.assistant {
            background: #f1f5f9;
            border-left: 4px solid var(--success-color);
        }
        
        .message.error {
            background: #fef2f2;
            border-left: 4px solid var(--danger-color);
            color: var(--danger-color);
        }
        
        .agent-badge {
            display: inline-block;
            background: var(--success-color);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        .input-field {
            flex: 1;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
        }
        
        .send-button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.2s;
        }
        
        .send-button:hover {
            background: #1d4ed8;
        }
        
        .send-button:disabled {
            background: var(--secondary-color);
            cursor: not-allowed;
        }
        
        .sidebar {
            background: var(--surface-color);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            height: fit-content;
        }
        
        .agent-list h3 {
            margin-bottom: 15px;
            color: var(--primary-color);
        }
        
        .agent-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            margin-bottom: 8px;
        }
        
        .agent-item.active {
            border-color: var(--success-color);
            background: #f0fdf4;
        }
        
        .agent-toggle {
            width: 40px;
            height: 20px;
            background: var(--secondary-color);
            border-radius: 10px;
            cursor: pointer;
            position: relative;
            transition: background-color 0.2s;
        }
        
        .agent-toggle.active {
            background: var(--success-color);
        }
        
        .agent-toggle::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: left 0.2s;
        }
        
        .agent-toggle.active::after {
            left: 22px;
        }
        
        .thinking-panel {
            background: #fefce8;
            border: 1px solid #facc15;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .thinking-header {
            font-weight: bold;
            color: #92400e;
            margin-bottom: 10px;
        }
        
        .thinking-trace {
            margin-bottom: 10px;
            padding: 8px;
            background: white;
            border-radius: 4px;
            font-size: 0.9em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-indicator.online {
            background: var(--success-color);
        }
        
        .status-indicator.offline {
            background: var(--danger-color);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: var(--secondary-color);
        }
        
        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: var(--danger-color);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 JuniorGPT - Secure AI Assistant</h1>
            <p>Multi-agent AI system with enhanced security and modular architecture</p>
        </header>
        
        <div class="main-content">
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message assistant">
                        <strong>JuniorGPT System:</strong><br>
                        Welcome! I'm your secure AI assistant with 14 specialized agents ready to help.
                        Type your message below to get started.
                    </div>
                </div>
                
                <div class="input-container">
                    <input 
                        type="text" 
                        id="messageInput" 
                        class="input-field" 
                        placeholder="Type your message here..."
                        maxlength="10000"
                        autocomplete="off"
                    />
                    <button id="sendButton" class="send-button">Send</button>
                </div>
                
                <div class="loading" id="loading">
                    <span>Processing your request...</span>
                </div>
            </div>
            
            <div class="sidebar">
                <div class="agent-list">
                    <h3>🔧 Active Agents</h3>
                    <div id="agentList">
                        <!-- Agents will be loaded here -->
                    </div>
                </div>
                
                <div class="thinking-panel" id="thinkingPanel" style="display: none;">
                    <div class="thinking-header">🧠 Agent Thinking Process</div>
                    <div id="thinkingContent">
                        <!-- Thinking traces will appear here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        class JuniorGPT {
            constructor() {
                this.conversationId = this.generateUUID();
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.messages = document.getElementById('messages');
                this.loading = document.getElementById('loading');
                this.agentList = document.getElementById('agentList');
                this.thinkingPanel = document.getElementById('thinkingPanel');
                this.thinkingContent = document.getElementById('thinkingContent');
                
                this.agents = {};
                this.isProcessing = false;
                
                this.init();
            }
            
            generateUUID() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    const r = Math.random() * 16 | 0;
                    const v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }
            
            async init() {
                await this.loadAgents();
                this.setupEventListeners();
            }
            
            setupEventListeners() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });
            }
            
            async loadAgents() {
                try {
                    const response = await fetch('/api/agents');
                    const agents = await response.json();
                    
                    this.agents = {};
                    this.agentList.innerHTML = '';
                    
                    agents.forEach(agent => {
                        this.agents[agent.agent_id] = agent;
                        this.createAgentElement(agent);
                    });
                } catch (error) {
                    console.error('Failed to load agents:', error);
                }
            }
            
            createAgentElement(agent) {
                const agentDiv = document.createElement('div');
                agentDiv.className = `agent-item ${agent.is_active ? 'active' : ''}`;
                agentDiv.innerHTML = `
                    <div>
                        <div style="font-weight: bold;">${agent.name}</div>
                        <div style="font-size: 0.8em; color: #64748b;">${agent.description}</div>
                    </div>
                    <div class="agent-toggle ${agent.is_active ? 'active' : ''}" 
                         onclick="app.toggleAgent('${agent.agent_id}')"></div>
                `;
                this.agentList.appendChild(agentDiv);
            }
            
            async toggleAgent(agentId) {
                try {
                    const agent = this.agents[agentId];
                    const newStatus = !agent.is_active;
                    
                    const response = await fetch('/api/agents/toggle', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
                        },
                        body: JSON.stringify({
                            agent_id: agentId,
                            active: newStatus
                        })
                    });
                    
                    if (response.ok) {
                        await this.loadAgents();
                    }
                } catch (error) {
                    console.error('Failed to toggle agent:', error);
                }
            }
            
            async sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message || this.isProcessing) return;
                
                this.isProcessing = true;
                this.updateUI(true);
                
                // Add user message to chat
                this.addMessage(message, 'user');
                this.messageInput.value = '';
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
                        },
                        body: JSON.stringify({
                            message: message,
                            conversation_id: this.conversationId
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        this.addMessage(data.response, 'assistant', data.agents_used);
                        this.showThinkingTraces(data.thinking_traces);
                    } else {
                        this.addMessage(data.error || 'An error occurred', 'error');
                    }
                    
                } catch (error) {
                    console.error('Error sending message:', error);
                    this.addMessage('Failed to send message. Please try again.', 'error');
                } finally {
                    this.isProcessing = false;
                    this.updateUI(false);
                }
            }
            
            addMessage(text, type, agents = []) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                let content = '';
                if (type === 'assistant' && agents && agents.length > 0) {
                    const agentBadges = agents.map(agentId => {
                        const agent = this.agents[agentId];
                        return `<span class="agent-badge">${agent ? agent.name : agentId}</span>`;
                    }).join('');
                    content = agentBadges + '<br>';
                }
                
                content += this.escapeHtml(text);
                messageDiv.innerHTML = content;
                
                this.messages.appendChild(messageDiv);
                this.messages.scrollTop = this.messages.scrollHeight;
            }
            
            showThinkingTraces(traces) {
                if (!traces || Object.keys(traces).length === 0) {
                    this.thinkingPanel.style.display = 'none';
                    return;
                }
                
                this.thinkingContent.innerHTML = '';
                
                Object.entries(traces).forEach(([agentId, trace]) => {
                    const traceDiv = document.createElement('div');
                    traceDiv.className = 'thinking-trace';
                    traceDiv.innerHTML = `
                        <strong>${trace.agent_name}:</strong><br>
                        ${this.escapeHtml(trace.thinking)}
                    `;
                    this.thinkingContent.appendChild(traceDiv);
                });
                
                this.thinkingPanel.style.display = 'block';
            }
            
            updateUI(processing) {
                this.sendButton.disabled = processing;
                this.messageInput.disabled = processing;
                this.loading.style.display = processing ? 'block' : 'none';
                
                if (processing) {
                    this.sendButton.textContent = 'Processing...';
                } else {
                    this.sendButton.textContent = 'Send';
                    this.messageInput.focus();
                }
            }
            
            escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;")
                    .replace(/\n/g, "<br>");
            }
        }
        
        // Initialize app when DOM is loaded
        let app;
        document.addEventListener('DOMContentLoaded', () => {
            app = new JuniorGPT();
        });
    </script>
</body>
</html>
'''

@app.before_request
def generate_csrf_token():
    """Generate CSRF token for each request"""
    if 'csrf_token' not in session:
        session['csrf_token'] = security.generate_csrf_token()

@app.route('/')
def home():
    """Main application route"""
    return render_template_string(HTML_TEMPLATE, csrf_token=session.get('csrf_token', ''))

@app.route('/api/agents')
def get_agents():
    """Get all active agents"""
    try:
        agents = agent_service.get_active_agents()
        return jsonify(agents)
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        return jsonify({"error": "Failed to load agents"}), 500

@app.route('/api/agents/toggle', methods=['POST'])
def toggle_agent():
    """Toggle agent active status"""
    # Validate CSRF token
    csrf_token = request.headers.get('X-CSRF-Token')
    if not security.validate_csrf_token(csrf_token, session.get('csrf_token')):
        return jsonify({"error": "Invalid CSRF token"}), 403
    
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        active = data.get('active', False)
        
        if not agent_id:
            return jsonify({"error": "Agent ID is required"}), 400
        
        success = agent_service.toggle_agent(agent_id, active)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to toggle agent"}), 400
            
    except Exception as e:
        logger.error(f"Failed to toggle agent: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    # Validate CSRF token
    csrf_token = request.headers.get('X-CSRF-Token')
    if not security.validate_csrf_token(csrf_token, session.get('csrf_token')):
        return jsonify({"error": "Invalid CSRF token"}), 403
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Validate message input
        is_valid, error_msg = security.validate_message_input(message)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Auto-detect agents
        detected_agents = agent_service.auto_detect_agents(message)
        
        # Get conversation history for context
        conversation_history = []
        if conversation_id:
            history = conversation_service.get_conversation_history(conversation_id, limit=10)
            conversation_history = [
                {
                    "user": conv["user_input"],
                    "assistant": conv["agent_response"]
                }
                for conv in history
            ]
        
        # Process with agents
        result = asyncio.run(agent_service.process_with_agents(
            message=message,
            agent_ids=detected_agents,
            conversation_id=conversation_id,
            conversation_history=conversation_history
        ))
        
        if result["success"]:
            # Save conversation
            saved_conversation_id = conversation_service.create_conversation(
                user_input=message,
                agent_response=result["response"],
                conversation_id=conversation_id,
                agents_used=result["agents_used"],
                response_time=result["response_time"],
                thinking_trace=result["thinking_traces"]
            )
            
            return jsonify({
                "success": True,
                "response": result["response"],
                "agents_used": result["agents_used"],
                "thinking_traces": result["thinking_traces"],
                "response_time": result["response_time"],
                "conversation_id": saved_conversation_id or conversation_id
            })
        else:
            return jsonify({
                "success": False,
                "error": result["error"],
                "response": result["response"]
            }), 500
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database
        with db.get_session() as session:
            session.execute("SELECT 1")
        
        # Check model service
        available_models = model_service.get_available_models()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "models": {
                "openai": len(available_models.get("openai", [])),
                "anthropic": len(available_models.get("anthropic", [])),
                "local": len(available_models.get("local", []))
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        conversation_stats = conversation_service.get_conversation_statistics()
        agent_stats = agent_service.get_agent_statistics()
        
        return jsonify({
            "conversations": conversation_stats,
            "agents": agent_stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Log startup information
    logger.info("Starting JuniorGPT application")
    logger.info(f"Configuration: {config.ENV}")
    logger.info(f"Database: {config.DATABASE_URL}")
    logger.info(f"Available models: {model_service.get_available_models()}")
    
    # Start the Flask application
    app.run(
        host='0.0.0.0',
        port=7860,
        debug=(config.ENV == 'development'),
        threaded=True
    )