#!/usr/bin/env python3
"""
JuniorGPT Security Setup Script

This script sets up secure configuration for JuniorGPT following Flask security best practices.
"""
import os
import secrets
from pathlib import Path

def setup_flask_security():
    """Set up Flask security configuration"""
    print("🔒 Setting up Flask Security for JuniorGPT")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📄 Creating .env from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
        else:
            print("❌ Neither .env nor .env.example found!")
            return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check current secret key
    current_key = None
    key_line_index = None
    
    for i, line in enumerate(lines):
        if line.startswith('FLASK_SECRET_KEY='):
            current_key = line.split('=', 1)[1].strip()
            key_line_index = i
            break
    
    print(f"📋 Current secret key: {'Set' if current_key and len(current_key) > 30 else 'Not properly set'}")
    
    # Check if key needs to be updated
    needs_update = False
    
    if not current_key:
        print("⚠️  No FLASK_SECRET_KEY found")
        needs_update = True
    elif current_key in ['your_generated_secret_key_here_minimum_32_characters_required', 
                         'your_super_secret_key_here_change_this_in_production']:
        print("⚠️  Using example secret key - needs to be changed!")
        needs_update = True
    elif len(current_key) < 32:
        print(f"⚠️  Secret key too short ({len(current_key)} chars, need 32+)")
        needs_update = True
    else:
        print("✅ Secret key appears to be properly set")
    
    if needs_update:
        # Generate new secure key
        new_key = secrets.token_hex(32)
        print(f"🔑 Generated new secure secret key (64 characters)")
        
        # Update .env file
        new_line = f"FLASK_SECRET_KEY={new_key}\n"
        
        if key_line_index is not None:
            lines[key_line_index] = new_line
        else:
            # Add new line
            lines.append(new_line)
        
        # Write updated content
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print("✅ Updated .env with new secure secret key")
    
    # Additional security checks
    print("\n🔍 Security Configuration Check:")
    
    # Check environment variables
    env_vars = {}
    for line in lines:
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    
    # Security recommendations
    security_checks = [
        ("CSRF_PROTECTION", "true", "CSRF protection enabled"),
        ("XSS_PROTECTION", "true", "XSS protection enabled"),
        ("FLASK_ENV", "development", "Environment set (use 'production' for live deployment)")
    ]
    
    for var_name, expected, description in security_checks:
        current_value = env_vars.get(var_name, "not set")
        status = "✅" if current_value == expected else "⚠️"
        print(f"   {status} {description}: {current_value}")
    
    # Production warnings
    if env_vars.get('FLASK_ENV') == 'production':
        print("\n🚨 PRODUCTION MODE DETECTED:")
        print("   - Ensure SECRET_KEY is cryptographically secure")
        print("   - Use HTTPS in production")
        print("   - Set up proper logging and monitoring")
        print("   - Review all environment variables")
    
    print("\n🛡️  Security Setup Complete!")
    return True

def verify_security_config():
    """Verify current security configuration"""
    print("\n🔍 Verifying Security Configuration...")
    
    try:
        from config import get_config
        config = get_config()
        
        # Check secret key
        if hasattr(config, 'SECRET_KEY'):
            key_length = len(config.SECRET_KEY)
            if key_length >= 32:
                print(f"✅ Secret key length: {key_length} characters (good)")
            else:
                print(f"⚠️  Secret key length: {key_length} characters (should be 32+)")
        
        # Check other security settings
        security_settings = [
            ('CSRF_PROTECTION', getattr(config, 'CSRF_PROTECTION', False)),
            ('XSS_PROTECTION', getattr(config, 'XSS_PROTECTION', False)),
            ('Environment', getattr(config, 'ENV', 'unknown'))
        ]
        
        for setting, value in security_settings:
            print(f"✅ {setting}: {value}")
        
        print("✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def create_security_checklist():
    """Create security checklist file"""
    checklist_content = """# JuniorGPT Security Checklist

## Development Security
- [ ] Generated secure FLASK_SECRET_KEY (32+ characters)
- [ ] Enabled CSRF protection
- [ ] Enabled XSS protection
- [ ] Using HTTPS for external API calls
- [ ] Input validation implemented
- [ ] SQL injection protection (parameterized queries)
- [ ] Sensitive data not logged
- [ ] API keys stored in environment variables only

## Production Security
- [ ] Change FLASK_ENV to 'production'
- [ ] Use strong, unique FLASK_SECRET_KEY
- [ ] Enable HTTPS/TLS encryption
- [ ] Set up proper logging and monitoring
- [ ] Configure rate limiting
- [ ] Review and audit all dependencies
- [ ] Set up backup systems
- [ ] Implement proper error handling
- [ ] Configure security headers
- [ ] Regular security updates

## API Key Security
- [ ] API keys stored in .env file only
- [ ] .env file added to .gitignore
- [ ] API keys never hardcoded in source
- [ ] Use minimum required permissions
- [ ] Regularly rotate API keys
- [ ] Monitor API usage for anomalies

## Database Security
- [ ] Use parameterized queries
- [ ] Regular database backups
- [ ] Restrict database access
- [ ] Encrypt sensitive data
- [ ] Monitor database access logs

## Infrastructure Security
- [ ] Keep system updated
- [ ] Use firewall protection
- [ ] Monitor system resources
- [ ] Set up intrusion detection
- [ ] Regular security audits

Generated by JuniorGPT Security Setup
"""
    
    checklist_file = Path("SECURITY_CHECKLIST.md")
    with open(checklist_file, 'w') as f:
        f.write(checklist_content)
    
    print(f"📋 Created security checklist: {checklist_file}")

def main():
    """Main security setup function"""
    print("🔐 JuniorGPT Security Setup")
    print("This script will help you set up secure configuration for your JuniorGPT installation.")
    print()
    
    # Setup Flask security
    if setup_flask_security():
        # Verify configuration
        verify_security_config()
        
        # Create security checklist
        create_security_checklist()
        
        print("\n🎉 Security setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Review the SECURITY_CHECKLIST.md file")
        print("2. Add your API keys to the .env file")
        print("3. Never commit the .env file to version control")
        print("4. For production: set FLASK_ENV=production")
        print("5. Use HTTPS in production environments")
        
    else:
        print("\n❌ Security setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()