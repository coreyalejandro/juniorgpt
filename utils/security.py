"""
Security utilities for JuniorGPT
"""
import html
import re
import secrets
from typing import Any, Dict, List, Optional
import bleach
from markupsafe import Markup

class SecurityUtils:
    """Security utilities for input sanitization and validation"""
    
    # Allowed HTML tags and attributes for message content
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitize HTML content to prevent XSS attacks"""
        if not content:
            return ""
            
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            content,
            tags=SecurityUtils.ALLOWED_TAGS,
            attributes=SecurityUtils.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    @staticmethod
    def escape_user_input(content: str) -> str:
        """Escape user input for safe HTML rendering"""
        if not content:
            return ""
            
        # HTML escape the content
        escaped = html.escape(content, quote=True)
        
        # Convert newlines to <br> tags
        escaped = escaped.replace('\n', '<br>')
        
        return Markup(escaped)
    
    @staticmethod
    def validate_message_input(message: str) -> tuple[bool, str]:
        """Validate user message input"""
        if not message or not message.strip():
            return False, "Message cannot be empty"
            
        if len(message) > 10000:  # 10KB limit
            return False, "Message too long (max 10,000 characters)"
            
        # Check for potential injection patterns
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "Message contains potentially unsafe content"
                
        return True, "Valid"
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        if not token or not session_token:
            return False
            
        return secrets.compare_digest(token, session_token)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        if not filename:
            return "untitled"
            
        # Remove path components and dangerous characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        safe_filename = safe_filename.replace('..', '').strip('. ')
        
        # Ensure not empty after sanitization
        if not safe_filename:
            safe_filename = "untitled"
            
        return safe_filename[:255]  # Limit length
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
            
        # Basic API key format validation
        if len(api_key) < 20 or len(api_key) > 200:
            return False
            
        # Should not contain spaces or special characters
        if re.search(r'[^a-zA-Z0-9_\-.]', api_key):
            return False
            
        return True
    
    @staticmethod
    def rate_limit_key(request) -> str:
        """Generate rate limit key from request"""
        # Use IP address for rate limiting
        forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.environ.get('REMOTE_ADDR', 'unknown')
            
        return f"rate_limit:{ip}"