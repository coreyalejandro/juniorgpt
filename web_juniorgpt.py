from flask import Flask, render_template_string, request, Response, jsonify
import requests
import json
import sqlite3
from datetime import datetime
import logging
import time
import os
from dotenv import load_dotenv
from agents.agent_registry import get_registry, discover_agents

from models import init_db
from services import TeamService

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_application():
    try:
        # Initialize persistent storage for teams
        init_db('sqlite:///data/teams.db')
        team_service = TeamService()

        # Initialize conversation database
        # (Add necessary initialization code)

        # Initialize agent registry and discover default agents
        agent_registry = get_registry()
        discover_agents(["agents/implementations"])
        
        # Initialize any additional databases
        # (Add any other needed initialization)

    except Exception as e:
        print(f"Initialization error: {e}")

# Run the initializer
initialize_application()
def init_database():
    conn = sqlite3.connect('data/conversations.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            conversation_id TEXT,
            timestamp TEXT,
            user_input TEXT,
            agent_response TEXT,
            agents_used TEXT,
            thinking_trace TEXT,
            satisfaction_rating INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Define the 14 specialized agents
AGENTS = {
    "research": {
        "name": "🔍 Research Agent",
        "description": "Deep research and information gathering",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I analyze information systematically, gathering facts and cross-referencing sources..."
    },
    "coding": {
        "name": "💻 Coding Agent", 
        "description": "Software development and debugging",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I write actual working code, build complete applications, and create runnable solutions. I focus on delivering executable code, not just explanations."
    },
    "analysis": {
        "name": "📊 Analysis Agent",
        "description": "Data analysis and insights",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I create actual data visualizations, build analysis scripts, and generate working charts and graphs. I deliver concrete analytical outputs, not just descriptions."
    },
    "writing": {
        "name": "✍️ Writing Agent",
        "description": "Content creation and editing",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I craft clear, engaging content with proper structure and flow..."
    },
    "planning": {
        "name": "📋 Planning Agent",
        "description": "Project planning and strategy",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I break down complex projects into manageable steps and create strategic roadmaps..."
    },
    "debugging": {
        "name": "🐛 Debugging Agent",
        "description": "Problem solving and troubleshooting",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I systematically identify root causes and develop systematic solutions..."
    },
    "creative": {
        "name": "🎨 Creative Agent",
        "description": "Creative ideation and design",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I build actual creative projects, generate visual designs, and create working prototypes. I deliver tangible creative outputs, not just concepts."
    },
    "learning": {
        "name": "📚 Learning Agent",
        "description": "Educational content and explanations",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I structure information for optimal learning and understanding..."
    },
    "communication": {
        "name": "💬 Communication Agent",
        "description": "Clear communication and summaries",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I create actual communication materials, build presentation tools, and generate working content. I deliver concrete communication outputs, not just advice."
    },
    "optimization": {
        "name": "⚡ Optimization Agent",
        "description": "Performance and efficiency improvements",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I identify bottlenecks and optimize for maximum efficiency and performance..."
    },
    "security": {
        "name": "🔒 Security Agent",
        "description": "Security analysis and recommendations",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I assess security risks and vulnerabilities with a security-first mindset..."
    },
    "testing": {
        "name": "🧪 Testing Agent",
        "description": "Testing strategies and validation",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I design comprehensive test strategies to ensure quality and reliability..."
    },
    "documentation": {
        "name": "📖 Documentation Agent",
        "description": "Documentation and technical writing",
        "model": "gpt-4o-mini",
        "active": True,
        "thinking_style": "I create clear, comprehensive documentation that serves user needs..."
    },
    "integration": {
        "name": "🔗 Integration Agent",
        "description": "System integration and APIs",
        "model": "claude-3-5-sonnet-20241022",
        "active": True,
        "thinking_style": "I design seamless integrations and API architectures..."
    }
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>JuniorGPT</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: #343541;
            color: #ececf1;
            height: 100vh;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
        }
        
        .main-content {
            display: flex;
            flex: 1;
        }
        
        /* Sidebar */
        .sidebar {
            width: 260px;
            background: #202123;
            border-right: 1px solid #4a4b53;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
        }
        
        .sidebar.collapsed {
            transform: translateX(-260px);
        }
        
        .sidebar-header {
            padding: 14px;
            border-bottom: 1px solid #4a4b53;
        }
        
        .new-chat-btn {
            width: 100%;
            padding: 12px;
            background: transparent;
            border: 1px solid #565869;
            border-radius: 6px;
            color: #ececf1;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .new-chat-btn:hover {
            background: #40414f;
        }
        
        .conversations-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }
        
        .conversation-item {
            padding: 10px 12px;
            margin-bottom: 2px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            color: #ececf1;
            transition: background 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .conversation-item:hover {
            background: #40414f;
        }
        
        .conversation-item.active {
            background: #40414f;
        }
        
        .conversation-title {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .conversation-meta {
            font-size: 11px;
            color: #8e8ea0;
            margin-left: auto;
        }
        
        .sidebar-footer {
            padding: 14px;
            border-top: 1px solid #4a4b53;
        }
        
        .settings-btn {
            width: 100%;
            padding: 10px;
            background: transparent;
            border: none;
            color: #ececf1;
            cursor: pointer;
            font-size: 14px;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 8px;
            border-radius: 6px;
            transition: background 0.2s ease;
        }
        
        .settings-btn:hover {
            background: #40414f;
        }
        
        /* Main Chat Area */
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #343541;
        }
        
        /* Thinking Panel */
        .thinking-panel {
            width: 300px;
            background: #202123;
            border-left: 1px solid #4a4b53;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .thinking-header {
            padding: 14px 16px;
            border-bottom: 1px solid #4a4b53;
            font-weight: 600;
            font-size: 14px;
            color: #ececf1;
        }
        
        .thinking-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .thinking-trace {
            background: #343541;
            border: 1px solid #4a4b53;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .thinking-agent {
            font-weight: 600;
            font-size: 12px;
            color: #19c37d;
            margin-bottom: 6px;
        }
        
        .thinking-text {
            font-size: 12px;
            line-height: 1.4;
            color: #ececf1;
        }
        
        .thinking-text.typing::after {
            content: '▋';
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        .chat-header {
            padding: 14px 20px;
            border-bottom: 1px solid #4a4b53;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .chat-title {
            font-size: 16px;
            font-weight: 600;
        }
        
        .toggle-sidebar-btn {
            background: transparent;
            border: none;
            color: #ececf1;
            cursor: pointer;
            padding: 8px;
            border-radius: 4px;
            transition: background 0.2s ease;
        }
        
        .toggle-sidebar-btn:hover {
            background: #40414f;
        }
        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 0;
        }
        
        .message {
            padding: 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            border-bottom: 1px solid #4a4b53;
        }
        
        .message.user {
            background: #343541;
        }
        
        .message.assistant {
            background: #444654;
        }
        
        .message-avatar {
            width: 30px;
            height: 30px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }
        
        .message-avatar.user {
            background: #10a37f;
        }
        
        .message-avatar.assistant {
            background: #19c37d;
        }
        
        .message-content {
            flex: 1;
            line-height: 1.6;
            font-size: 16px;
        }
        
        .message-content p {
            margin-bottom: 12px;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        .message-attachments {
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .message-attachment {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px;
            background: #2a2a2a;
            border-radius: 8px;
            border: 1px solid #565869;
        }
        
        .agent-indicator {
            font-size: 12px;
            color: #8e8ea0;
            margin-bottom: 8px;
            font-style: italic;
        }
        
        .input-container {
            padding: 20px;
            border-top: 1px solid #4a4b53;
            background: #343541;
        }
        
        .input-wrapper {
            max-width: 768px;
            margin: 0 auto;
            position: relative;
            display: flex;
            align-items: flex-end;
            gap: 8px;
            background: #40414f;
            border-radius: 12px;
            padding: 12px;
            border: 1px solid #565869;
        }
        
        .input-actions {
            display: flex;
            gap: 4px;
            margin-right: 8px;
        }
        
        .action-btn {
            background: none;
            border: none;
            color: #8e8ea0;
            padding: 6px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .action-btn:hover {
            background: #565869;
            color: #ffffff;
        }
        
        .action-btn.recording {
            background: #ef4444;
            color: #ffffff;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .attachments-container {
            margin-top: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .attachment-item {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #2a2a2a;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #565869;
            font-size: 12px;
            color: #8e8ea0;
        }
        
        .attachment-item img {
            width: 40px;
            height: 40px;
            object-fit: cover;
            border-radius: 4px;
        }
        
        .attachment-remove {
            background: none;
            border: none;
            color: #ef4444;
            cursor: pointer;
            padding: 2px;
            border-radius: 4px;
        }
        
        .attachment-remove:hover {
            background: #ef4444;
            color: #ffffff;
        }
        
        .message-input {
            width: 100%;
            padding: 12px 45px 12px 16px;
            background: #40414f;
            border: 1px solid #565869;
            border-radius: 6px;
            color: #ececf1;
            font-size: 16px;
            line-height: 1.5;
            resize: none;
            outline: none;
            transition: border-color 0.2s ease;
            min-height: 44px;
            max-height: 200px;
        }
        
        .message-input:focus {
            border-color: #19c37d;
        }
        
        .send-button {
            position: absolute;
            right: 8px;
            bottom: 8px;
            background: #19c37d;
            border: none;
            border-radius: 4px;
            width: 28px;
            height: 28px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s ease;
        }
        
        .send-button:hover {
            background: #1a7f64;
        }
        
        .send-button:disabled {
            background: #565869;
            cursor: not-allowed;
        }
        
        /* Settings Modal */
        .settings-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .settings-modal.active {
            display: flex;
        }
        
        .settings-content {
            background: #40414f;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            padding: 24px;
        }
        
        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #565869;
        }
        
        .settings-title {
            font-size: 20px;
            font-weight: 600;
        }
        
        .close-settings {
            background: transparent;
            border: none;
            color: #ececf1;
            cursor: pointer;
            font-size: 20px;
            padding: 4px;
        }
        
        .settings-section {
            margin-bottom: 24px;
        }
        
        .settings-section h3 {
            margin-bottom: 12px;
            font-size: 16px;
            font-weight: 600;
        }

        .team-management {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .team-management select,
        .team-management input {
            padding: 8px;
            border: 1px solid #565869;
            border-radius: 4px;
            background: #40414f;
            color: #ececf1;
        }

        .team-buttons {
            display: flex;
            gap: 8px;
        }

        .team-buttons button {
            padding: 8px 12px;
            background: transparent;
            border: 1px solid #565869;
            color: #ececf1;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }
        
        .agent-card {
            background: #343541;
            border: 1px solid #565869;
            border-radius: 6px;
            padding: 16px;
            transition: border-color 0.2s ease;
        }
        
        .agent-card.active {
            border-color: #19c37d;
        }
        
        .agent-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .agent-name {
            font-weight: 600;
            font-size: 14px;
        }
        
        .agent-toggle {
            position: relative;
            width: 40px;
            height: 20px;
            background: #565869;
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        
        .agent-toggle.active {
            background: #19c37d;
        }
        
        .agent-toggle::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s ease;
        }
        
        .agent-toggle.active::after {
            transform: translateX(20px);
        }
        
        .agent-description {
            font-size: 12px;
            color: #8e8ea0;
            margin-bottom: 8px;
        }
        
        .agent-model {
            font-size: 11px;
            color: #565869;
        }
        
        .auto-mode-section {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 0;
            border-bottom: 1px solid #565869;
        }
        
        .auto-mode-label {
            font-weight: 500;
        }
        
        .auto-mode-description {
            font-size: 12px;
            color: #8e8ea0;
            margin-top: 4px;
        }
        
        /* Model Selection Styles */
        .model-selection-section {
            margin-bottom: 20px;
        }
        
        .model-option {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            background: #2a2a2a;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .model-option:hover {
            background: #3a3a3a;
        }
        
        .model-option input[type="radio"] {
            margin-right: 12px;
            accent-color: #10a37f;
        }
        
        .model-option-label {
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 4px;
        }
        
        .model-option-description {
            font-size: 12px;
            color: #a0a0a0;
        }
        
        .model-list {
            margin-top: 15px;
            padding: 15px;
            background: #1a1a1a;
            border-radius: 8px;
            border: 1px solid #333;
        }
        
        .model-category {
            margin-bottom: 20px;
        }
        
        .model-category h4 {
            color: #10a37f;
            margin-bottom: 10px;
            font-size: 14px;
            font-weight: 600;
        }
        
        .model-checkbox {
            display: block;
            margin-bottom: 8px;
            padding: 8px;
            border-radius: 6px;
            background: #2a2a2a;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .model-checkbox:hover {
            background: #3a3a3a;
        }
        
        .model-checkbox input[type="checkbox"] {
            margin-right: 8px;
            accent-color: #10a37f;
        }
        
        /* Loading Animation */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 8px 0;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #8e8ea0;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                z-index: 100;
            }
            
            .main-chat {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <button class="new-chat-btn" onclick="startNewConversation()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"/>
                    </svg>
                    New chat
                </button>
            </div>
            
            <div class="conversations-list" id="conversationsList">
                <!-- Conversations will be populated here -->
            </div>
            
            <div class="sidebar-footer">
                <button class="settings-btn" onclick="openSettings()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                    Settings
                </button>
            </div>
        </div>
        
        <!-- Main Content Area -->
        <div class="main-content">
            <!-- Main Chat Area -->
            <div class="main-chat">
                <div class="chat-header">
                    <div class="chat-title" id="chatTitle">New conversation</div>
                    <button class="toggle-sidebar-btn" onclick="toggleSidebar()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="3" y1="6" x2="21" y2="6"/>
                            <line x1="3" y1="12" x2="21" y2="12"/>
                            <line x1="3" y1="18" x2="21" y2="18"/>
                        </svg>
                    </button>
                </div>
                
                <div class="messages-container" id="messagesContainer">
                    <div class="message assistant">
                        <div class="message-avatar assistant">🤖</div>
                        <div class="message-content">
                            <div class="agent-indicator">JuniorGPT System</div>
                            <p>Hello! I'm JuniorGPT, your AI assistant with 14 specialized agents. I can help you with research, coding, analysis, writing, planning, and much more. What would you like to work on today?</p>
                        </div>
                    </div>
                </div>
                
                <div class="input-container">
                    <div class="input-wrapper">
                        <div class="input-actions">
                            <button class="action-btn" onclick="document.getElementById('fileInput').click()" title="Upload file">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                                </svg>
                            </button>
                            <button class="action-btn" onclick="document.getElementById('imageInput').click()" title="Upload image">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                    <circle cx="8.5" cy="8.5" r="1.5"/>
                                    <path d="M21 15l-5-5L5 21"/>
                                </svg>
                            </button>
                            <button class="action-btn" onclick="startVoiceInput()" title="Voice input">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/>
                                </svg>
                            </button>
                        </div>
                        <textarea 
                            class="message-input" 
                            id="messageInput" 
                            placeholder="Message JuniorGPT... (supports text, images, files, voice)" 
                            rows="1"
                            onkeydown="handleKeyDown(event)"
                            oninput="autoResize(this)"
                        ></textarea>
                        <button class="send-button" id="sendButton" onclick="sendMessage()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="attachments-container" id="attachmentsContainer">
                        <!-- Attachments will be shown here -->
                    </div>
                </div>
                
                <!-- Hidden file inputs -->
                <input type="file" id="fileInput" multiple accept=".txt,.pdf,.doc,.docx,.csv,.json,.py,.js,.html,.css,.md" style="display: none;" onchange="handleFileUpload(event)">
                <input type="file" id="imageInput" multiple accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
            </div>
            
            <!-- Thinking Panel -->
            <div class="thinking-panel" id="thinkingPanel">
                <div class="thinking-header">
                    🧠 Agent Thinking Process
                </div>
                <div class="thinking-content" id="thinkingContent">
                    <div class="thinking-trace">
                        <div class="thinking-agent">System</div>
                        <div class="thinking-text">Waiting for your input... I'll show you each agent's thinking process in real-time as they work on your request.</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div class="settings-modal" id="settingsModal">
        <div class="settings-content">
            <div class="settings-header">
                <div class="settings-title">Settings</div>
                <button class="close-settings" onclick="closeSettings()">×</button>
            </div>
            
            <div class="settings-section">
                <div class="auto-mode-section">
                    <div>
                        <div class="auto-mode-label">Auto-Detect Agents</div>
                        <div class="auto-mode-description">Automatically select the best agents for your requests</div>
                    </div>
                    <div class="agent-toggle" id="autoModeToggle" onclick="toggleAutoMode()"></div>
                </div>
            </div>

            <div class="settings-section">
                <h3>Teams</h3>
                <div class="team-management">
                    <select id="teamSelect" onchange="onTeamSelect()"></select>
                    <input type="text" id="teamName" placeholder="Team name">
                    <div class="team-buttons">
                        <button onclick="saveTeam()">Save Team</button>
                        <button onclick="deleteTeam()">Delete Team</button>
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h3>Agent Configuration</h3>
                <div class="agent-grid" id="agentGrid">
                    <!-- Agents will be populated here -->
                </div>
            </div>
            
            <div class="settings-section">
                <h3>Model Selection</h3>
                <div class="model-selection-section">
                    <div class="model-option">
                        <input type="radio" name="model-selection" id="auto-models" value="auto" checked>
                        <label for="auto-models">
                            <div class="model-option-label">Auto-pilot</div>
                            <div class="model-option-description">Best model per agent (recommended)</div>
                        </label>
                    </div>
                    <div class="model-option">
                        <input type="radio" name="model-selection" id="manual-models" value="manual">
                        <label for="manual-models">
                            <div class="model-option-label">Manual selection</div>
                            <div class="model-option-description">Choose specific models</div>
                        </label>
                    </div>
                </div>
                
                <div class="model-list" id="modelList" style="display: none;">
                    <div class="model-category">
                        <h4>OpenAI Models</h4>
                        <label class="model-checkbox"><input type="checkbox" value="gpt-4o-mini"> GPT-4o Mini (Fast & Cost-effective)</label>
                        <label class="model-checkbox"><input type="checkbox" value="gpt-4o"> GPT-4o (Most Capable)</label>
                        <label class="model-checkbox"><input type="checkbox" value="gpt-3.5-turbo"> GPT-3.5 Turbo (Fastest)</label>
                    </div>
                    <div class="model-category">
                        <h4>Anthropic Models</h4>
                        <label class="model-checkbox"><input type="checkbox" value="claude-3-5-sonnet-20241022"> Claude 3.5 Sonnet (Balanced)</label>
                        <label class="model-checkbox"><input type="checkbox" value="claude-3-haiku"> Claude 3 Haiku (Fast)</label>
                        <label class="model-checkbox"><input type="checkbox" value="claude-3-opus"> Claude 3 Opus (Most Capable)</label>
                    </div>
                    <div class="model-category">
                        <h4>Local Models (Ollama)</h4>
                        <label class="model-checkbox"><input type="checkbox" value="llama2"> Llama2 (Free)</label>
                        <label class="model-checkbox"><input type="checkbox" value="llama2:13b"> Llama2 13B (Better)</label>
                        <label class="model-checkbox"><input type="checkbox" value="codellama:13b"> CodeLlama 13B (Code-focused)</label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedAgents = [];
        let currentTeamId = '';
        let autoMode = true;
        let isProcessing = false;
        let currentConversationId = '';
        let conversationHistory = [];
        let modelSelectionMode = 'auto';
        let selectedModels = [];
        let attachments = [];
        let mediaRecorder = null;
        let audioChunks = [];
        let agents = ''' + json.dumps(AGENTS).replace('\\', '\\\\') + ''';
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initializeAgents();
            loadConversations();
            loadTeams();
            updateAutoModeToggle();
            initializeModelSelection();
        });
        
        function initializeAgents() {
            const agentGrid = document.getElementById('agentGrid');
            Object.keys(agents).forEach(agentId => {
                const agent = agents[agentId];
                const agentCard = document.createElement('div');
                agentCard.className = 'agent-card';
                agentCard.id = 'agent-' + agentId;

                agentCard.innerHTML = `
                    <div class="agent-header">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-toggle" onclick="toggleAgent('${agentId}')"></div>
                    </div>
                    <div class="agent-description">${agent.description}</div>
                    <div class="agent-model">Model: ${agent.model}</div>
                `;

                agentGrid.appendChild(agentCard);
            });
            updateAgentCardsFromSelection();
        }
        
        function toggleAgent(agentId) {
            if (autoMode) return;

            currentTeamId = '';
            document.getElementById('teamSelect').value = '';
            document.getElementById('teamName').value = '';

            const agentCard = document.getElementById('agent-' + agentId);
            const toggle = agentCard.querySelector('.agent-toggle');
            const isActive = agentCard.classList.contains('active');

            if (isActive) {
                agentCard.classList.remove('active');
                toggle.classList.remove('active');
                selectedAgents = selectedAgents.filter(id => id !== agentId);
            } else {
                agentCard.classList.add('active');
                toggle.classList.add('active');
                selectedAgents.push(agentId);
            }
        }
        
        function toggleAutoMode() {
            autoMode = !autoMode;
            updateAutoModeToggle();
            
            if (autoMode) {
                // Clear manual selections
                selectedAgents = [];
                currentTeamId = '';
                document.getElementById('teamSelect').value = '';
                document.getElementById('teamName').value = '';
                document.querySelectorAll('.agent-card').forEach(card => {
                    card.classList.remove('active');
                    card.querySelector('.agent-toggle').classList.remove('active');
                });
            }
        }

        function loadTeams() {
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('teamSelect');
                    if (!select) return;
                    select.innerHTML = '<option value="">-- Select Team --</option>';
                    data.forEach(team => {
                        const opt = document.createElement('option');
                        opt.value = team.team_id;
                        opt.textContent = team.name;
                        select.appendChild(opt);
                    });
                });
        }

        function onTeamSelect() {
            const select = document.getElementById('teamSelect');
            const teamId = select.value;
            if (!teamId) {
                currentTeamId = '';
                document.getElementById('teamName').value = '';
                selectedAgents = [];
                updateAgentCardsFromSelection();
                return;
            }

            fetch('/api/teams/' + teamId)
                .then(response => response.json())
                .then(team => {
                    currentTeamId = team.team_id;
                    document.getElementById('teamName').value = team.name;
                    selectedAgents = team.agents || [];
                    autoMode = false;
                    updateAutoModeToggle();
                    updateAgentCardsFromSelection();
                });
        }

        function updateAgentCardsFromSelection() {
            document.querySelectorAll('.agent-card').forEach(card => {
                const agentId = card.id.replace('agent-', '');
                const toggle = card.querySelector('.agent-toggle');
                if (selectedAgents.includes(agentId)) {
                    card.classList.add('active');
                    toggle.classList.add('active');
                } else {
                    card.classList.remove('active');
                    toggle.classList.remove('active');
                }
            });
        }

        function saveTeam() {
            const name = document.getElementById('teamName').value.trim();
            if (!name) return;
            const payload = { name: name, agents: selectedAgents };
            if (currentTeamId) payload.team_id = currentTeamId;
            fetch('/api/teams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(team => {
                currentTeamId = team.team_id;
                loadTeams();
                document.getElementById('teamSelect').value = team.team_id;
            });
        }

        function deleteTeam() {
            if (!currentTeamId) return;
            fetch('/api/teams/' + currentTeamId, { method: 'DELETE' })
                .then(() => {
                    currentTeamId = '';
                    document.getElementById('teamName').value = '';
                    document.getElementById('teamSelect').value = '';
                    selectedAgents = [];
                    updateAgentCardsFromSelection();
                    loadTeams();
                });
        }
        
        function updateAutoModeToggle() {
            const toggle = document.getElementById('autoModeToggle');
            if (autoMode) {
                toggle.classList.add('active');
            } else {
                toggle.classList.remove('active');
            }
        }
        
        function initializeModelSelection() {
            // Handle model selection mode changes
            document.querySelectorAll('input[name="model-selection"]').forEach(radio => {
                radio.addEventListener('change', function() {
                    modelSelectionMode = this.value;
                    const modelList = document.getElementById('modelList');
                    if (modelSelectionMode === 'manual') {
                        modelList.style.display = 'block';
                    } else {
                        modelList.style.display = 'none';
                        selectedModels = [];
                    }
                });
            });
            
            // Handle model checkbox changes
            document.querySelectorAll('.model-checkbox input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        selectedModels.push(this.value);
                    } else {
                        selectedModels = selectedModels.filter(model => model !== this.value);
                    }
                });
            });
        }
        
        // Multimodal handling functions
        function handleFileUpload(event) {
            const files = Array.from(event.target.files);
            files.forEach(file => {
                attachments.push({
                    file: file,
                    name: file.name,
                    type: 'file',
                    size: file.size
                });
            });
            updateAttachmentsDisplay();
            event.target.value = '';
        }
        
        function handleImageUpload(event) {
            const files = Array.from(event.target.files);
            files.forEach(file => {
                if (file.type.startsWith('image/')) {
                    attachments.push({
                        file: file,
                        name: file.name,
                        type: 'image',
                        size: file.size
                    });
                }
            });
            updateAttachmentsDisplay();
            event.target.value = '';
        }
        
        function updateAttachmentsDisplay() {
            const container = document.getElementById('attachmentsContainer');
            container.innerHTML = '';
            
            attachments.forEach((attachment, index) => {
                const item = document.createElement('div');
                item.className = 'attachment-item';
                
                if (attachment.type === 'image') {
                    const img = document.createElement('img');
                    img.src = URL.createObjectURL(attachment.file);
                    item.appendChild(img);
                }
                
                const name = document.createElement('span');
                name.textContent = attachment.name;
                item.appendChild(name);
                
                const removeBtn = document.createElement('button');
                removeBtn.className = 'attachment-remove';
                removeBtn.innerHTML = '×';
                removeBtn.onclick = () => removeAttachment(index);
                item.appendChild(removeBtn);
                
                container.appendChild(item);
            });
        }
        
        function removeAttachment(index) {
            attachments.splice(index, 1);
            updateAttachmentsDisplay();
        }
        
        function startVoiceInput() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('Voice input is not supported in your browser');
                return;
            }
            
            const voiceBtn = document.querySelector('.action-btn[onclick="startVoiceInput()"]');
            
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                // Stop recording
                mediaRecorder.stop();
                voiceBtn.classList.remove('recording');
                return;
            }
            
            // Start recording
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const audioFile = new File([audioBlob], 'voice_input.wav', { type: 'audio/wav' });
                        
                        attachments.push({
                            file: audioFile,
                            name: 'Voice Input',
                            type: 'audio',
                            size: audioFile.size
                        });
                        
                        updateAttachmentsDisplay();
                        
                        // Stop all tracks
                        stream.getTracks().forEach(track => track.stop());
                    };
                    
                    mediaRecorder.start();
                    voiceBtn.classList.add('recording');
                })
                .catch(err => {
                    console.error('Error accessing microphone:', err);
                    alert('Error accessing microphone. Please check permissions.');
                });
        }
        
        function openSettings() {
            document.getElementById('settingsModal').classList.add('active');
        }
        
        function closeSettings() {
            document.getElementById('settingsModal').classList.remove('active');
        }
        
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('collapsed');
        }
        
        function startNewConversation() {
            currentConversationId = '';
            conversationHistory = [];
            document.getElementById('messagesContainer').innerHTML = `
                <div class="message assistant">
                    <div class="message-avatar assistant">🤖</div>
                    <div class="message-content">
                        <div class="agent-indicator">JuniorGPT System</div>
                        <p>Hello! I'm JuniorGPT, your AI assistant with 14 specialized agents. I can help you with research, coding, analysis, writing, planning, and much more. What would you like to work on today?</p>
                    </div>
                </div>
            `;
            document.getElementById('chatTitle').textContent = 'New conversation';
            document.getElementById('messageInput').value = '';
        }
        
        function loadConversations() {
            // Load conversations from the database
            fetch('/api/conversations')
                .then(response => response.json())
                .then(conversations => {
                    const conversationsList = document.getElementById('conversationsList');
                    conversationsList.innerHTML = '';
                    
                    conversations.forEach(conv => {
                        const convItem = document.createElement('div');
                        convItem.className = 'conversation-item';
                        convItem.onclick = () => loadConversation(conv.id);
                        convItem.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            </svg>
                            <div class="conversation-title">${conv.title}</div>
                            <div class="conversation-meta">${conv.message_count} messages</div>
                        `;
                        conversationsList.appendChild(convItem);
                    });
                })
                .catch(error => {
                    console.error('Error loading conversations:', error);
                });
        }
        
        function loadConversation(conversationId) {
            // Load conversation messages from the database
            currentConversationId = conversationId;
            
            // Clear current messages
            document.getElementById('messagesContainer').innerHTML = '';
            
            fetch(`/api/conversations/${conversationId}`)
                .then(response => response.json())
                .then(messages => {
                    messages.forEach(msg => {
                        // Add user message
                        addMessage(msg.user_input, true);
                        
                        // Add assistant response
                        addMessage(msg.agent_response, false, msg.agents_used);
                    });
                    
                    document.getElementById('chatTitle').textContent = 'Previous conversation';
                })
                .catch(error => {
                    console.error('Error loading conversation:', error);
                });
        }
        
        function saveConversation(title) {
            const savedConversations = JSON.parse(localStorage.getItem('conversations') || '[]');
            savedConversations.unshift({
                id: currentConversationId,
                title: title,
                timestamp: new Date().toISOString()
            });
            localStorage.setItem('conversations', JSON.stringify(savedConversations.slice(0, 50))); // Keep last 50
            loadConversations();
        }
        
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        }
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function addMessage(content, isUser = false, agentName = null, attachments = []) {
            const messagesContainer = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (isUser ? 'user' : 'assistant');
            
            const avatar = isUser ? '👤' : '🤖';
            const avatarClass = isUser ? 'user' : 'assistant';
            
            let agentIndicator = '';
            if (agentName) {
                agentIndicator = `<div class="agent-indicator">${agentName}</div>`;
            }
            
            let attachmentsHtml = '';
            if (attachments && attachments.length > 0) {
                attachmentsHtml = '<div class="message-attachments">';
                attachments.forEach(attachment => {
                    if (attachment.type === 'image') {
                        attachmentsHtml += `<div class="message-attachment"><img src="${URL.createObjectURL(attachment.file)}" style="max-width: 300px; max-height: 300px; border-radius: 8px;"></div>`;
                    } else if (attachment.type === 'file') {
                        attachmentsHtml += `<div class="message-attachment"><div style="font-size: 24px;">📄</div><div style="font-size: 12px; color: #8e8ea0;">${attachment.name}</div></div>`;
                    } else if (attachment.type === 'audio') {
                        attachmentsHtml += `<div class="message-attachment"><div style="font-size: 24px;">🎤</div><div style="font-size: 12px; color: #8e8ea0;">${attachment.name}</div></div>`;
                    }
                });
                attachmentsHtml += '</div>';
            }
            
            messageDiv.innerHTML = `
                <div class="message-avatar ${avatarClass}">${avatar}</div>
                <div class="message-content">
                    ${agentIndicator}
                    <p>${content || ''}</p>
                    ${attachmentsHtml}
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function addTypingIndicator() {
            const messagesContainer = document.getElementById('messagesContainer');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';
            
            typingDiv.innerHTML = `
                <div class="message-avatar assistant">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function removeTypingIndicator() {
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
        
        function addThinkingTrace(agentName, thinking, isTyping = false) {
            const thinkingContent = document.getElementById('thinkingContent');
            const traceDiv = document.createElement('div');
            traceDiv.className = 'thinking-trace';
            traceDiv.id = 'thinking-' + agentName.replace(/\s+/g, '-').toLowerCase();
            
            traceDiv.innerHTML = `
                <div class="thinking-agent">${agentName}</div>
                <div class="thinking-text${isTyping ? ' typing' : ''}">${thinking}</div>
            `;
            
            thinkingContent.appendChild(traceDiv);
            thinkingContent.scrollTop = thinkingContent.scrollHeight;
        }
        
        function updateThinkingTrace(agentName, thinking) {
            const traceId = 'thinking-' + agentName.replace(/\s+/g, '-').toLowerCase();
            let traceDiv = document.getElementById(traceId);
            
            if (!traceDiv) {
                addThinkingTrace(agentName, thinking);
            } else {
                const textElement = traceDiv.querySelector('.thinking-text');
                textElement.textContent = thinking;
                textElement.classList.remove('typing');
            }
        }
        
        function clearThinkingTraces() {
            const thinkingContent = document.getElementById('thinkingContent');
            thinkingContent.innerHTML = `
                <div class="thinking-trace">
                    <div class="thinking-agent">System</div>
                    <div class="thinking-text">Waiting for your input... I'll show you each agent's thinking process in real-time as they work on your request.</div>
                </div>
            `;
        }
        
        function sendMessage() {
            if (isProcessing) return;
            
            const input = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const message = input.value.trim();
            
            if (!message && attachments.length === 0) return;
            
            isProcessing = true;
            sendButton.disabled = true;
            input.disabled = true;
            
            // Add user message with attachments
            addMessage(message, true, null, attachments);
            
            // Clear input and attachments
            input.value = '';
            attachments = [];
            updateAttachmentsDisplay();
            autoResize(input);
            
            // Clear thinking traces and add typing indicator
            clearThinkingTraces();
            addTypingIndicator();
            
            // Send to backend with streaming
            const eventSource = new EventSource('/stream_chat?message=' + encodeURIComponent(message) + '&auto_mode=' + autoMode + '&selected_agents=' + JSON.stringify(selectedAgents) + '&team_id=' + currentTeamId + '&conversation_id=' + currentConversationId);
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'agent_start') {
                    addThinkingTrace(data.agent_name, data.thinking, true);
                }
                else if (data.type === 'agent_thinking') {
                    updateThinkingTrace(data.agent_name, data.thinking);
                }
                else if (data.type === 'agent_response') {
                    // Handle complete agent response
                    const agentName = data.agent_name;
                    const response = data.response;
                    
                    // Add the agent's response to the chat
                    addMessage(response, false, agentName);
                    
                    // Update thinking trace
                    updateThinkingTrace(agentName, 'Response complete');
                }
                else if (data.type === 'final_response') {
                    removeTypingIndicator();
                    addMessage(data.response, false, data.agents_used);
                    
                    // Update conversation history
                    currentConversationId = data.conversation_id;
                    conversationHistory.push({
                        user: message,
                        assistant: data.response,
                        agents: data.agents_used
                    });
                    
                    // Save conversation if it's new
                    if (conversationHistory.length === 1) {
                        saveConversation(message.substring(0, 50) + (message.length > 50 ? '...' : ''));
                        document.getElementById('chatTitle').textContent = message.substring(0, 30) + (message.length > 30 ? '...' : '');
                    }
                    
                    eventSource.close();
                    
                    // Reset UI
                    isProcessing = false;
                    sendButton.disabled = false;
                    input.disabled = false;
                }
                else if (data.type === 'error') {
                    removeTypingIndicator();
                    addMessage('Error: ' + data.error, false);
                    eventSource.close();
                    
                    // Reset UI
                    isProcessing = false;
                    sendButton.disabled = false;
                    input.disabled = false;
                }
            };
            
            eventSource.onerror = function() {
                removeTypingIndicator();
                addMessage('Connection error. Please try again.', false);
                eventSource.close();
                
                // Reset UI
                isProcessing = false;
                sendButton.disabled = false;
                input.disabled = false;
            };
        }
        
        // Close settings when clicking outside
        document.getElementById('settingsModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeSettings();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/teams', methods=['GET', 'POST'])
def manage_teams():
    """Create new teams or list existing ones"""
    if request.method == 'GET':
        return jsonify(team_service.list_teams())

    data = request.get_json() or {}
    name = data.get('name')
    agents = data.get('agents', [])
    team_id = data.get('team_id')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if team_id:
        team = team_service.update_team(team_id, name=name, agents=agents)
    else:
        team = team_service.create_team(name, agents)
    return jsonify(team)


@app.route('/api/teams/<team_id>', methods=['GET', 'DELETE'])
def team_detail(team_id):
    """Retrieve or delete a specific team"""
    if request.method == 'GET':
        team = team_service.get_team(team_id)
        if team:
            return jsonify(team)
        return jsonify({'error': 'Not found'}), 404

    deleted = team_service.delete_team(team_id)
    return jsonify({'success': deleted})

@app.route('/api/conversations')
def get_conversations():
    """Get all conversations for the sidebar"""
    try:
        conn = sqlite3.connect('data/conversations.db')
        cursor = conn.execute('''
            SELECT DISTINCT conversation_id, 
                   MIN(timestamp) as first_message,
                   MAX(timestamp) as last_message,
                   COUNT(*) as message_count
            FROM conversations 
            GROUP BY conversation_id 
            ORDER BY last_message DESC
        ''')
        conversations = []
        for row in cursor.fetchall():
            conversation_id, first_msg, last_msg, count = row
            # Get the first user message as title
            title_cursor = conn.execute('''
                SELECT user_input FROM conversations 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC LIMIT 1
            ''', (conversation_id,))
            title_row = title_cursor.fetchone()
            title = title_row[0][:50] + "..." if title_row and len(title_row[0]) > 50 else (title_row[0] if title_row else "New Conversation")
            
            conversations.append({
                'id': conversation_id,
                'title': title,
                'timestamp': last_msg,
                'message_count': count
            })
        conn.close()
        return jsonify(conversations)
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return jsonify([])

@app.route('/api/conversations/<conversation_id>')
def get_conversation_messages(conversation_id):
    """Get all messages for a specific conversation"""
    try:
        conn = sqlite3.connect('data/conversations.db')
        cursor = conn.execute('''
            SELECT user_input, agent_response, agents_used, timestamp
            FROM conversations 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        messages = []
        for row in cursor.fetchall():
            user_input, agent_response, agents_used, timestamp = row
            messages.append({
                'user_input': user_input,
                'agent_response': agent_response,
                'agents_used': agents_used,
                'timestamp': timestamp
            })
        conn.close()
        return jsonify(messages)
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        return jsonify([])

@app.route('/stream_chat')
def stream_chat():
    message = request.args.get('message', '')
    auto_mode = request.args.get('auto_mode', 'true').lower() == 'true'
    conversation_id = request.args.get('conversation_id', '')

# Parse team ID and selected agents from query parameters with error handling
team_id = request.args.get('team_id')

# Initialize selected_agents to an empty list
selected_agents = []

# Attempt to parse selected agents, with error handling
try:
    selected_agents = json.loads(request.args.get('selected_agents', '[]'))
    if not isinstance(selected_agents, list):
        logger.error("selected_agents parameter is not a list")
        selected_agents = []
except json.JSONDecodeError as e:
    logger.error(f"Error parsing selected_agents: {e}")

# If team_id is provided, retrieve agents from the team
if team_id:
    team = team_service.get_team(team_id)
    if team and team.get('agents'):
        selected_agents = team['agents']

# Set auto_mode to False if valid team agents are found
auto_mode = not bool(selected_agents)
    # Generate new conversation ID if not provided
    if not conversation_id:
        conversation_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def generate():
        try:

    # Determine which agents to use
if auto_mode:
    agents_to_use = auto_detect_agents(message)
else:
    # Use selected agents if provided; fallback to default agent if not
    agents_to_use = selected_agents if selected_agents else [next(iter(AGENTS))]
    
    if not selected_agents:
        logger.info("No selected_agents provided; falling back to default agent")

            # Process with each agent in real-time
            final_response = ""
            agents_used = []

    # Use the selected agents or auto-detected agents
for agent_id in agents_to_use:
    # Process each agent_id as needed
                if agent_id in AGENTS:
                    agent = AGENTS[agent_id]
                    agents_used.append(agent['name'])
                    
                    # Send agent start
                    yield f"data: {json.dumps({'type': 'agent_start', 'agent_name': agent['name'], 'thinking': 'Starting ' + agent['name'] + ' analysis...'})}\n\n"
                    
                    # Simulate thinking process with internet search
                    thinking_steps = [
                        f"Analyzing request with {agent['name']} expertise...",
                        "Searching internet for up-to-date information...",
                        f"Applying {agent['thinking_style']}",
                        f"Processing {agent['description']}...",
                        f"Generating response using {agent['model']}..."
                    ]
                    
                    for i, thinking in enumerate(thinking_steps):
                        yield f"data: {json.dumps({'type': 'agent_thinking', 'agent_name': agent['name'], 'thinking': thinking})}\n\n"
                        
                        # Perform internet search on the second step
                        if i == 1:  # "Searching internet for up-to-date information..."
                            try:
                                search_results = search_internet(message)
                                yield f"data: {json.dumps({'type': 'agent_thinking', 'agent_name': agent['name'], 'thinking': f'Found recent information: {search_results[:200]}...'})}\n\n"
                            except Exception:
                                yield "data: " + json.dumps({'type': 'agent_thinking', 'agent_name': agent['name'], 'thinking': 'Search completed for up-to-date information...'}) + "\n\n"
                        
                        time.sleep(1)  # Show thinking for 1 second each step
                    
                    # Get actual response from model with streaming
                    try:
                        # Get search results for this agent
                        try:
                            search_results = search_internet(message)
                        except Exception:
                            search_results = f"Search completed for: {message}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
                        
                        enhanced_prompt = f"""You are {agent['name']}. {agent['description']}. {agent['thinking_style']}

CRITICAL INSTRUCTION: You are an ACTION-ORIENTED agent. When users ask you to create, build, or generate something, you MUST provide actual working code, files, or deliverables - NOT just instructions or explanations. Always default to building the actual thing requested.

RECENT INTERNET SEARCH RESULTS:
{search_results}

USER REQUEST: {message}

RESPONSE REQUIREMENTS:
1. If the user asks for code, applications, visualizations, or any deliverables - PROVIDE THE ACTUAL WORKING CODE/FILES
2. Write complete, runnable code with all necessary imports and dependencies
3. Include sample data when needed
4. Provide working examples that users can execute immediately
5. Do NOT just give instructions - BUILD THE ACTUAL THING
6. If you cannot build something due to limitations, clearly state what you CAN build and provide that instead

Remember: You are a BUILDER, not just an advisor. Create actual working solutions."""
                        
                        # Get conversation history for context
                        conversation_history = get_conversation_history(conversation_id)
                        
                        # Get response from model
                        agent_response = ""
                        try:
                            # Get conversation history for context
                            conversation_history = get_conversation_history(conversation_id)
                            
                            # Use the model response function
                            agent_response = get_model_response(agent['model'], enhanced_prompt, conversation_history)
                            
                            # Send the complete response
                            yield f"data: {json.dumps({'type': 'agent_response', 'agent_name': agent['name'], 'response': agent_response})}\n\n"
                            
                        except Exception as e:
                            agent_response = f"Error: {str(e)}"
                            yield "data: " + json.dumps({'type': 'agent_response', 'agent_name': agent['name'], 'response': agent_response}) + "\n\n"
                        
                        final_response += f"[{agent['name']}]: {agent_response}\n\n"
                            
                    except Exception as e:
                        agent_response = f"Error: {str(e)}"
                        final_response += f"[{agent['name']}]: {agent_response}\n\n"
                    
                    # Send agent response
                    yield f"data: {json.dumps({'type': 'agent_response', 'agent_name': agent['name'], 'response': agent_response})}\n\n"
                    
                    # Small delay between agents
                    time.sleep(0.5)
            
            # Send final response
            yield f"data: {json.dumps({'type': 'final_response', 'response': final_response.strip(), 'agents_used': agents_used, 'conversation_id': conversation_id})}\n\n"
            
            # Save to database
            save_conversation(message, {
                'response': final_response.strip(),
                'agents_used': agents_used,
                'thinking_traces': []
            }, conversation_id)
            
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

def auto_detect_agents(message):
    """Auto-detect relevant agents using the global registry"""
    selected = agent_registry.auto_select_agents(message)
    if not selected:
        selected = ['communication']
    return selected

def save_conversation(user_input, response, conversation_id):
    """Save conversation to database"""
    try:
        conn = sqlite3.connect('data/conversations.db')
        conn.execute('''
            INSERT INTO conversations 
            (conversation_id, timestamp, user_input, agent_response, agents_used, thinking_trace)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            conversation_id,
            datetime.now().isoformat(),
            user_input,
            response['response'],
            json.dumps(response['agents_used']),
            json.dumps([])
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")

def get_conversation_history(conversation_id):
    """Get conversation history for context"""
    try:
        if not conversation_id:
            return []
            
        conn = sqlite3.connect('data/conversations.db')
        cursor = conn.execute('''
            SELECT user_input, agent_response FROM conversations 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

def get_model_response(model_name, prompt, conversation_history=None):
    """Get response from different model types (Ollama, OpenAI, Anthropic)"""
    try:
        # Check if it's a cloud model
        if model_name.startswith(('gpt-', 'claude-')):
            return get_cloud_model_response(model_name, prompt, conversation_history)
        else:
            # Local Ollama model
            return get_ollama_response(model_name, prompt)
    except Exception as e:
        logger.error(f"Error getting response from {model_name}: {e}")
        return f"Error: Unable to get response from {model_name}. Please check your API configuration."

def get_cloud_model_response(model_name, prompt, conversation_history=None):
    """Get response from OpenAI or Anthropic models"""
    try:
        if model_name.startswith('gpt-'):
            # OpenAI API
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment variables."
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            if conversation_history:
                for user_input, agent_response in conversation_history:
                    messages.append({"role": "user", "content": user_input})
                    messages.append({"role": "assistant", "content": agent_response})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                'model': model_name,
                'messages': messages,
                'max_tokens': 2000,
                'temperature': 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"OpenAI API Error: {response.status_code} - {response.text}"
                
        elif model_name.startswith('claude-'):
            # Anthropic API
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return "Error: ANTHROPIC_API_KEY not found in environment variables."
            
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Build conversation context
            conversation_text = ""
            if conversation_history:
                for user_input, agent_response in conversation_history:
                    conversation_text += f"\n\nHuman: {user_input}\n\nAssistant: {agent_response}"
            conversation_text += f"\n\nHuman: {prompt}"
            
            data = {
                'model': model_name,
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': conversation_text}]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                return f"Anthropic API Error: {response.status_code} - {response.text}"
                
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error with cloud model {model_name}")
        return f"Error: Request to {model_name} timed out. Please try again or check your internet connection."
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error with cloud model {model_name}")
        return f"Error: Unable to connect to {model_name}. Please check your internet connection and API configuration."
    except Exception as e:
        logger.error(f"Error with cloud model {model_name}: {e}")
        return f"Error: Unable to connect to {model_name}. Please check your API configuration."

def get_ollama_response(model_name, prompt):
    """Get response from local Ollama model"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            return f"Ollama Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error with Ollama model {model_name}")
        return f"Error: Request to Ollama model {model_name} timed out. Please try again."
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error with Ollama model {model_name}")
        return f"Error: Unable to connect to Ollama model {model_name}. Please ensure Ollama is running on localhost:11434."
    except Exception as e:
        logger.error(f"Error with Ollama model {model_name}: {e}")
        return f"Error: Unable to connect to Ollama model {model_name}. Please ensure Ollama is running."

def stream_cloud_model_response(model_name, prompt, conversation_history, agent_name):
    """Stream response from OpenAI or Anthropic models"""
    try:
        if model_name.startswith('gpt-'):
            # OpenAI streaming
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment variables."
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            if conversation_history:
                for user_input, agent_response in conversation_history:
                    messages.append({"role": "user", "content": user_input})
                    messages.append({"role": "assistant", "content": agent_response})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                'model': model_name,
                'messages': messages,
                'max_tokens': 2000,
                'temperature': 0.7,
                'stream': True
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str != '[DONE]':
                                try:
                                    chunk = json.loads(data_str)
                                    if 'choices' in chunk and chunk['choices']:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            content = delta['content']
                                            full_response += content
                                            yield f"data: {json.dumps({'type': 'agent_response_chunk', 'agent_name': agent_name, 'content': content})}\n\n"
                                except json.JSONDecodeError:
                                    continue
                return full_response
            else:
                return f"OpenAI API Error: {response.status_code}"
                
        elif model_name.startswith('claude-'):
            # Anthropic streaming
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return "Error: ANTHROPIC_API_KEY not found in environment variables."
            
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            conversation_text = ""
            if conversation_history:
                for user_input, agent_response in conversation_history:
                    conversation_text += f"\n\nHuman: {user_input}\n\nAssistant: {agent_response}"
            conversation_text += f"\n\nHuman: {prompt}"
            
            data = {
                'model': model_name,
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': conversation_text}],
                'stream': True
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str != '[DONE]':
                                try:
                                    chunk = json.loads(data_str)
                                    if chunk.get('type') == 'content_block_delta':
                                        content = chunk['delta']['text']
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'agent_response_chunk', 'agent_name': agent_name, 'content': content})}\n\n"
                                except json.JSONDecodeError:
                                    continue
                return full_response
            else:
                return f"Anthropic API Error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"Error streaming from cloud model {model_name}: {e}")
        return f"Error: Unable to stream from {model_name}."

def stream_ollama_response(model_name, prompt, agent_name):
    """Stream response from local Ollama model"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": True
            },
            timeout=60,
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            content = chunk['response']
                            full_response += content
                            yield f"data: {json.dumps({'type': 'agent_response_chunk', 'agent_name': agent_name, 'content': content})}\n\n"
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            return full_response
        else:
            return f"Ollama Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error streaming from Ollama model {model_name}: {e}")
        return f"Error: Unable to stream from Ollama model {model_name}."

def search_internet(query, max_results=5):
    """Search the internet for up-to-date information"""
    try:
        # Use DuckDuckGo Instant Answer API for search
        search_url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(search_url, params=params, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Extract relevant information
                results = []
                
                # Add abstract if available
                if data and data.get('Abstract'):
                    results.append(f"Abstract: {data['Abstract']}")
                
                # Add related topics
                if data and data.get('RelatedTopics'):
                    for topic in data['RelatedTopics'][:3]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(f"Related: {topic['Text']}")
                
                # Add answer if available
                if data and data.get('Answer'):
                    results.append(f"Answer: {data['Answer']}")
                
                # If no results from DuckDuckGo, provide a fallback
                if not results:
                    search_results = f"Web search for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
                    results.append(search_results)
                
                return "\n\n".join(results) if results else f"No recent information found for: {query}"
                
            except json.JSONDecodeError:
                return f"Search completed for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
        else:
            return f"Search completed for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error searching internet for: {query}")
        return f"Search timeout for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error searching internet for: {query}")
        return f"Search connection error for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."
    except Exception as e:
        logger.error(f"Error searching internet: {e}")
        return f"Search completed for: {query}\n\nFor the most up-to-date information, I recommend checking recent sources on this topic."

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    print("🤖 JuniorGPT ChatGPT-Style Interface Starting...")
    print("Open your browser and go to: http://localhost:8080")
    print("Features:")
    print("- ChatGPT-like interface")
    print("- 14 Specialized Agents")
    print("- Conversation history")
    print("- Settings panel for agent configuration")
    print("- Auto-agent detection")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
