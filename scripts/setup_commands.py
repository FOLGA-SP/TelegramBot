#!/usr/bin/env python3
"""
Setup script to configure bot commands.
Configures the bot's menu commands that appear in the Telegram interface.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application
from telegram import BotCommand

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_bot_commands():
    """Configure bot commands for the Telegram menu button."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        print("🤖 Setting up bot commands...")
        
        # Define available commands with multilingual descriptions
        commands = [
            BotCommand("start", "🚀 Start the bot / Запустить бота / Uruchom bota"),
            BotCommand("menu", "📋 Main menu / Главное меню / Menu główne"),
            BotCommand("contact", "📞 Contact info / Контакты / Kontakt"),
            BotCommand("language", "🌐 Change language / Сменить язык / Zmień język"),
            BotCommand("cancel", "❌ Cancel & return to menu / Отмена в меню / Anuluj do menu")
        ]
        
        await application.bot.set_my_commands(commands)
        
        print("✅ Successfully set up bot commands!")
        print("\n📱 Available commands:")
        for cmd in commands:
            print(f"   /{cmd.command} - {cmd.description}")
        
        print("\n🔄 Commands are now available in the bot menu.")
        
    except Exception as e:
        print(f"❌ Error setting up bot commands: {e}")
        logger.error(f"Error setting up bot commands: {e}")

async def verify_commands():
    """Verify that commands are configured correctly."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        print("\n🔍 Verifying commands setup...")
        
        commands = await application.bot.get_my_commands()
        
        if commands:
            print(f"✅ Found {len(commands)} commands:")
            for cmd in commands:
                print(f"   /{cmd.command} - {cmd.description}")
        else:
            print("❌ No commands found!")
        
        print("\n✅ Command verification complete!")
        
    except Exception as e:
        print(f"❌ Error verifying commands: {e}")

async def main():
    """Main function to configure and verify commands."""
    await setup_bot_commands()
    await verify_commands()

if __name__ == "__main__":
    print("🚀 Setting up Telegram Bot Commands...")
    asyncio.run(main()) 