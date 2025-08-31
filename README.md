# JuniorGPT - Enhanced Secure Multi-Agent AI Assistant

## 🚀 Overview

JuniorGPT is a secure, modular multi-agent AI assistant that combines the power of 14 specialized AI agents with enterprise-grade security features. This enhanced version addresses critical security vulnerabilities and implements a robust, maintainable architecture.

## ✨ Key Improvements

### 🔒 Security Enhancements

- **Environment-based configuration** - No more hardcoded API keys
- **Input sanitization** - XSS protection with HTML sanitization
- **CSRF protection** - Token-based request validation
- **SQL injection prevention** - Parameterized queries with SQLAlchemy ORM
- **Rate limiting support** - Built-in rate limiting utilities
- **Secure logging** - Sensitive data filtering in logs

### 🏗️ Architecture Improvements

- **Modular design** - Separated concerns into services, models, and utilities
- **Database ORM** - SQLAlchemy with proper relationships and migrations
- **Async support** - Asynchronous processing for better performance
- **Error handling** - Comprehensive error management and logging
- **Configuration management** - Environment-based settings with validation

### 📊 Enhanced Features

- **Performance tracking** - Agent execution metrics and response times
- **Conversation management** - Advanced search, tagging, and archiving
- **Real-time thinking traces** - Visual agent thinking process
- **Health monitoring** - System health checks and statistics
- **Database migrations** - Smooth upgrades from legacy versions

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Ollama (for local models) - optional
- OpenAI API key
- Anthropic API key

### Quick Start

1. **Clone and setup**

   ```bash
   cd juniorgpt
   pip install -r requirements.txt
   ```

2. **Set up security (generates secure Flask secret key)**

   ```bash
   python setup_security.py
   ```

3. **Configure environment**

   ```bash
   # .env file is created automatically by security setup
   # Edit .env with your API keys:
   nano .env
   # Add your OPENAI_API_KEY and ANTHROPIC_API_KEY
   ```

4. **Initialize database**

   ```bash
   python migrate.py --migrate  # If upgrading from old version
   # OR
   python migrate.py --sample-data  # For fresh installation with sample data
   ```

5. **Run the application**

   ```bash
   # For plugin-based architecture (recommended):
   python app_plugin.py
   
   # For original architecture:
   python app.py
   ```

6. **Access the interface**
   - Open <http://localhost:7860> in your browser
   - Start chatting with your AI assistants!

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///data/conversations.db
DATABASE_ECHO=false

# Ollama Configuration (for local models)
OLLAMA_HOST=localhost:11434
OLLAMA_TIMEOUT=60

# Security
FLASK_SECRET_KEY=your_super_secret_key_here
CSRF_PROTECTION=true
XSS_PROTECTION=true

# Application Settings
LOG_LEVEL=INFO
MAX_CONTEXT_LENGTH=8192
RESPONSE_TIMEOUT=60
```

### Agent Configuration

The system includes 14 specialized agents:

- 🔍 **Research Agent** - Information gathering and analysis
- 💻 **Coding Agent** - Software development and debugging
- 📊 **Analysis Agent** - Data analysis and insights
- ✍️ **Writing Agent** - Content creation and editing
- 🎨 **Creative Agent** - Creative tasks and brainstorming
- 📋 **Planning Agent** - Project planning and organization
- 🧩 **Problem Solver** - Complex problem analysis
- 💬 **Communication Agent** - Communication assistance
- 🔢 **Math Agent** - Mathematical calculations
- 🎓 **Learning Agent** - Educational content
- 💼 **Business Agent** - Business strategy
- 🏥 **Health Agent** - Health and wellness information
- ⚖️ **Legal Agent** - Legal information and guidance
- 🔧 **Technical Agent** - Technical support

## 📖 API Reference

### Chat Endpoint

```http
POST /api/chat
Content-Type: application/json
X-CSRF-Token: <token>

{
  "message": "Your message here",
  "conversation_id": "optional-conversation-id"
}
```

### Agent Management

```http
GET /api/agents
POST /api/agents/toggle
```

### System Health

```http
GET /api/health
GET /api/stats
```

## 🚀 Usage Examples

### Basic Chat

```python
import requests

response = requests.post('http://localhost:7860/api/chat', 
    json={
        "message": "Help me write a Python function to calculate fibonacci numbers",
        "conversation_id": "my-conversation"
    },
    headers={'X-CSRF-Token': csrf_token}
)

result = response.json()
print(result['response'])
```

### Agent Toggle

```python
requests.post('http://localhost:7860/api/agents/toggle',
    json={
        "agent_id": "coding",
        "active": True
    },
    headers={'X-CSRF-Token': csrf_token}
)
```

## 🔄 Migration from Legacy Version

If upgrading from the original `web_juniorgpt.py`:

1. **Backup your data**

   ```bash
   cp data/conversations.db data/conversations.db.backup
   ```

2. **Run migration**

   ```bash
   python migrate.py --migrate
   ```

3. **Verify migration**

   ```bash
   python app.py
   # Check that your conversations are preserved
   ```

## 📊 Database Schema

### Conversations

- Enhanced conversation tracking with metadata
- Tagging and archiving support
- Performance metrics
- User feedback integration

### Agents

- Agent configuration storage
- Performance tracking
- Execution history

### Agent Executions

- Detailed execution logs
- Performance metrics
- Error tracking

## 🧪 Testing

```bash
# Run basic tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 📈 Monitoring

### Health Checks

- Database connectivity
- Model availability
- System resources

### Performance Metrics

- Response times
- Agent usage statistics
- Error rates
- Token usage

### Logging

- Structured logging with security filtering
- Separate error logs
- Configurable log levels

## 🔒 Security Best Practices

### Automated Security Setup

```bash
# One-command security setup
python setup_security.py
```

This automatically:

- Generates cryptographically secure Flask secret key (64 characters)
- Creates/updates .env file with secure defaults
- Validates security configuration
- Creates security checklist

### Manual Security Setup

```bash
# Generate secure secret key only
python generate_secret_key.py
```

### Security Guidelines

1. **Never commit API keys** - Use environment variables only
2. **Secure secret keys** - Use 32+ character cryptographically random keys
3. **Regular security updates** - Keep dependencies updated  
4. **Monitor logs** - Check for suspicious activity
5. **Backup data** - Regular database backups
6. **Network security** - Use HTTPS in production
7. **Environment separation** - Different keys for dev/staging/production

### Security Documentation

- 📋 **[Complete Security Setup Guide](SECURITY_SETUP_README.md)** - Comprehensive security documentation
- ✅ **[Security Checklist](SECURITY_CHECKLIST.md)** - Generated security checklist (created after running `setup_security.py`)

## 🛡️ Security Features

- **Input validation** - All user inputs are validated and sanitized
- **XSS protection** - HTML content is escaped and sanitized
- **CSRF protection** - All state-changing requests require CSRF tokens
- **SQL injection prevention** - Parameterized queries only
- **Rate limiting** - Built-in rate limiting support
- **Secure headers** - Security headers for web requests
- **Data encryption** - Sensitive data encryption at rest

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run security checks
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation Issues**: Check this README and code comments
- **Bug Reports**: Create an issue with detailed reproduction steps
- **Feature Requests**: Suggest enhancements via issues
- **Security Issues**: Report via private channel

## 🔮 Roadmap

### Short Term

- [ ] WebSocket support for real-time streaming
- [ ] Advanced rate limiting with Redis
- [ ] User authentication and authorization
- [ ] API key management interface

### Medium Term

- [ ] Multi-tenant support
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom agents
- [ ] Docker containerization

### Long Term

- [ ] Kubernetes deployment
- [ ] Advanced ML model integration
- [ ] Federation with other AI systems
- [ ] Enterprise SSO integration

---

## ⚡ Quick Commands

```bash
# Start development server
python app.py

# Run database migration
python migrate.py --migrate

# Create sample data
python migrate.py --sample-data

# Health check
curl http://localhost:7860/api/health

# View logs
tail -f logs/juniorgpt.log
```

# Built with ❤️ for secure, scalable AI assistance
