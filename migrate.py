"""
Database migration script for JuniorGPT
Migrate existing data from the old schema to the new enhanced schema
"""
import sqlite3
import json
import sys
import os
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from models import init_db, Conversation, Agent
from utils.logging_config import setup_logging

def migrate_database():
    """Migrate existing database to new schema"""
    
    config = get_config()
    logger = setup_logging(config.LOG_LEVEL, include_console=True)
    
    logger.info("Starting database migration...")
    
    # Check if old database exists
    old_db_path = 'data/conversations.db'
    if not os.path.exists(old_db_path):
        logger.warning(f"Old database not found at {old_db_path}")
        logger.info("Creating new database with fresh schema...")
        
        # Initialize new database
        db = init_db(config.DATABASE_URL, config.DATABASE_ECHO)
        logger.info("New database created successfully")
        return
    
    # Create backup of old database
    backup_path = f"{old_db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(old_db_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    try:
        # Initialize new database
        logger.info("Initializing new database schema...")
        db = init_db(config.DATABASE_URL, config.DATABASE_ECHO)
        
        # Connect to old database
        logger.info("Reading data from old database...")
        old_conn = sqlite3.connect(old_db_path)
        old_conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Migrate conversations
        migrate_conversations(old_conn, db, logger)
        
        old_conn.close()
        logger.info("Database migration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def migrate_conversations(old_conn, db, logger):
    """Migrate conversation data"""
    
    try:
        # Get old conversations
        cursor = old_conn.cursor()
        cursor.execute("""
            SELECT id, conversation_id, timestamp, user_input, agent_response, 
                   agents_used, thinking_trace, satisfaction_rating
            FROM conversations
            ORDER BY timestamp
        """)
        
        old_conversations = cursor.fetchall()
        logger.info(f"Found {len(old_conversations)} conversations to migrate")
        
        migrated_count = 0
        
        with db.get_session() as session:
            for old_conv in old_conversations:
                try:
                    # Parse JSON fields safely
                    agents_used = []
                    thinking_trace = {}
                    
                    if old_conv['agents_used']:
                        try:
                            agents_used = json.loads(old_conv['agents_used'])
                        except (json.JSONDecodeError, TypeError):
                            agents_used = []
                    
                    if old_conv['thinking_trace']:
                        try:
                            thinking_trace = json.loads(old_conv['thinking_trace'])
                        except (json.JSONDecodeError, TypeError):
                            thinking_trace = {}
                    
                    # Parse timestamp
                    timestamp = old_conv['timestamp']
                    if timestamp:
                        try:
                            created_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            created_at = datetime.utcnow()
                    else:
                        created_at = datetime.utcnow()
                    
                    # Create new conversation
                    new_conversation = Conversation(
                        user_input=old_conv['user_input'] or '',
                        agent_response=old_conv['agent_response'] or '',
                        conversation_id=old_conv['conversation_id'] or f"migrated_{old_conv['id']}",
                        agents_used=agents_used,
                        thinking_trace=thinking_trace,
                        satisfaction_rating=old_conv['satisfaction_rating']
                    )
                    
                    # Set the timestamp manually
                    new_conversation.created_at = created_at
                    new_conversation.updated_at = created_at
                    
                    session.add(new_conversation)
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} conversations...")
                        session.commit()  # Commit in batches
                
                except Exception as e:
                    logger.warning(f"Failed to migrate conversation {old_conv['id']}: {e}")
                    continue
            
            session.commit()
        
        logger.info(f"Successfully migrated {migrated_count} conversations")
        
    except Exception as e:
        logger.error(f"Failed to migrate conversations: {e}")
        raise

def create_sample_data():
    """Create some sample data for testing"""
    
    config = get_config()
    logger = setup_logging(config.LOG_LEVEL, include_console=True)
    
    logger.info("Creating sample data...")
    
    try:
        db = init_db(config.DATABASE_URL, config.DATABASE_ECHO)
        
        with db.get_session() as session:
            # Create sample conversations
            sample_conversations = [
                {
                    "user_input": "Hello, can you help me write a Python function?",
                    "agent_response": "Of course! I'd be happy to help you write a Python function. What specific functionality are you looking to implement?",
                    "agents_used": ["coding"],
                    "model_used": "claude-3-5-sonnet",
                    "response_time": 2.3
                },
                {
                    "user_input": "I need to research the latest trends in AI development",
                    "agent_response": "I'll help you research the latest AI development trends. Let me gather information on recent advancements, emerging technologies, and industry insights.",
                    "agents_used": ["research"],
                    "model_used": "gpt-4o-mini",
                    "response_time": 3.1
                },
                {
                    "user_input": "Can you analyze this data and write a report about it?",
                    "agent_response": "I'll analyze your data and create a comprehensive report. I'll examine patterns, trends, and provide actionable insights in a well-structured document.",
                    "agents_used": ["analysis", "writing"],
                    "model_used": "gpt-4o",
                    "response_time": 4.7
                }
            ]
            
            for conv_data in sample_conversations:
                conversation = Conversation(
                    user_input=conv_data["user_input"],
                    agent_response=conv_data["agent_response"],
                    agents_used=conv_data.get("agents_used", []),
                    model_used=conv_data.get("model_used", ""),
                    response_time=conv_data.get("response_time", 0.0)
                )
                session.add(conversation)
            
            session.commit()
            logger.info(f"Created {len(sample_conversations)} sample conversations")
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JuniorGPT Database Migration Tool')
    parser.add_argument('--migrate', action='store_true', help='Migrate existing database')
    parser.add_argument('--sample-data', action='store_true', help='Create sample data')
    parser.add_argument('--force', action='store_true', help='Force migration (skip confirmations)')
    
    args = parser.parse_args()
    
    if args.migrate:
        if not args.force:
            response = input("This will migrate your existing database. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                sys.exit(0)
        
        success = migrate_database()
        sys.exit(0 if success else 1)
    
    elif args.sample_data:
        create_sample_data()
    
    else:
        parser.print_help()