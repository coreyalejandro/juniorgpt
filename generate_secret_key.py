#!/usr/bin/env python3
"""
Flask Secret Key Generator for JuniorGPT

This script generates cryptographically secure secret keys for Flask applications
using the recommended methods from the tutorials.
"""
import secrets
import uuid
import os
from pathlib import Path

def generate_secret_key_hex(length: int = 32) -> str:
    """
    Generate a secure secret key using hexadecimal encoding.
    
    Args:
        length: Number of bytes for the key (default: 32)
        
    Returns:
        Hexadecimal string representation of the secret key
    """
    return secrets.token_hex(length)

def generate_secret_key_urlsafe(length: int = 32) -> str:
    """
    Generate a secure secret key using URL-safe base64 encoding.
    
    Args:
        length: Number of bytes for the key (default: 32)
        
    Returns:
        URL-safe base64 string representation of the secret key
    """
    return secrets.token_urlsafe(length)

def generate_secret_key_uuid() -> str:
    """
    Generate a secret key using UUID4 (alternative method).
    
    Returns:
        Hexadecimal string representation of UUID4
    """
    return uuid.uuid4().hex

def update_env_file(secret_key: str, env_file_path: str = ".env") -> bool:
    """
    Update or create .env file with the generated secret key.
    
    Args:
        secret_key: The generated secret key
        env_file_path: Path to the .env file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        env_path = Path(env_file_path)
        
        # Read existing .env file if it exists
        env_content = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.readlines()
        
        # Update or add FLASK_SECRET_KEY
        updated = False
        for i, line in enumerate(env_content):
            if line.startswith('FLASK_SECRET_KEY='):
                env_content[i] = f'FLASK_SECRET_KEY={secret_key}\n'
                updated = True
                break
        
        # Add FLASK_SECRET_KEY if not found
        if not updated:
            env_content.append(f'FLASK_SECRET_KEY={secret_key}\n')
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(env_content)
        
        print(f"✅ Updated {env_file_path} with new FLASK_SECRET_KEY")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {env_file_path}: {e}")
        return False

def main():
    """Main function to generate and display secret keys"""
    print("🔐 Flask Secret Key Generator for JuniorGPT")
    print("=" * 50)
    
    # Generate different types of secret keys
    print("\n1. Hexadecimal Secret Key (Recommended):")
    hex_key = generate_secret_key_hex(32)
    print(f"   {hex_key}")
    
    print("\n2. URL-Safe Base64 Secret Key:")
    urlsafe_key = generate_secret_key_urlsafe(32)
    print(f"   {urlsafe_key}")
    
    print("\n3. UUID-based Secret Key:")
    uuid_key = generate_secret_key_uuid()
    print(f"   {uuid_key}")
    
    print("\n" + "=" * 50)
    print("📝 Recommended: Use the hexadecimal key (option 1)")
    print("🔒 Keep this key secret and never commit it to version control!")
    
    # Ask user which key to use
    print("\nWould you like to update the .env file with the hexadecimal key? (y/n): ", end="")
    try:
        choice = input().lower().strip()
        if choice in ['y', 'yes']:
            # Check if .env exists, if not create from example
            env_path = Path(".env")
            env_example_path = Path(".env.example")
            
            if not env_path.exists() and env_example_path.exists():
                print("📄 .env file not found, creating from .env.example...")
                import shutil
                shutil.copy(env_example_path, env_path)
            
            # Update with new secret key
            success = update_env_file(hex_key)
            
            if success:
                print(f"✅ Secret key has been saved to .env file")
                print("🚀 You can now run your Flask application securely!")
            else:
                print("❌ Failed to update .env file")
                print(f"💡 Manually add this line to your .env file:")
                print(f"   FLASK_SECRET_KEY={hex_key}")
        else:
            print(f"💡 To use the key manually, add this to your .env file:")
            print(f"   FLASK_SECRET_KEY={hex_key}")
            
    except (EOFError, KeyboardInterrupt):
        print(f"\n💡 To use the key manually, add this to your .env file:")
        print(f"   FLASK_SECRET_KEY={hex_key}")

if __name__ == "__main__":
    main()