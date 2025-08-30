"""
Configuration management for JuniorGPT
"""
import os
import secrets
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def _generate_fallback_secret_key() -> str:
    """Generate a secure fallback secret key if none is provided"""
    # Only generate fallback for development, require explicit key for production
    if os.environ.get('FLASK_ENV') == 'production':
        return 'PRODUCTION-KEY-REQUIRED-SET-FLASK_SECRET_KEY'
    else:
        # Generate a secure random key for development
        return secrets.token_hex(32)

class Config:
    """Base configuration class"""
    
    # API Keys
    OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY: str = os.environ.get('ANTHROPIC_API_KEY', '')
    
    # Database
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite:///data/conversations.db')
    DATABASE_ECHO: bool = os.environ.get('DATABASE_ECHO', 'false').lower() == 'true'
    
    # Ollama
    OLLAMA_HOST: str = os.environ.get('OLLAMA_HOST', 'localhost:11434')
    OLLAMA_TIMEOUT: int = int(os.environ.get('OLLAMA_TIMEOUT', '60'))
    
    # Flask
    SECRET_KEY: str = os.environ.get('FLASK_SECRET_KEY', _generate_fallback_secret_key())
    ENV: str = os.environ.get('FLASK_ENV', 'development')
    
    # Security
    CSRF_PROTECTION: bool = os.environ.get('CSRF_PROTECTION', 'true').lower() == 'true'
    XSS_PROTECTION: bool = os.environ.get('XSS_PROTECTION', 'true').lower() == 'true'
    
    # Performance
    MAX_CONTEXT_LENGTH: int = int(os.environ.get('MAX_CONTEXT_LENGTH', '8192'))
    RESPONSE_TIMEOUT: int = int(os.environ.get('RESPONSE_TIMEOUT', '60'))
    MAX_CONCURRENT_REQUESTS: int = int(os.environ.get('MAX_CONCURRENT_REQUESTS', '10'))
    
    # Features
    AUTO_DETECT_AGENTS: bool = os.environ.get('AUTO_DETECT_AGENTS', 'true').lower() == 'true'
    ENABLE_INTERNET_SEARCH: bool = os.environ.get('ENABLE_INTERNET_SEARCH', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.environ.get('LOG_FILE', 'logs/juniorgpt.log')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
            
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required")
            
        if cls.SECRET_KEY == 'PRODUCTION-KEY-REQUIRED-SET-FLASK_SECRET_KEY' and cls.ENV == 'production':
            errors.append("FLASK_SECRET_KEY must be set in production environment")
            
        if cls.ENV == 'production' and len(cls.SECRET_KEY) < 32:
            errors.append("FLASK_SECRET_KEY should be at least 32 characters long in production")
            
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
            
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DATABASE_ECHO = False
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    
# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])