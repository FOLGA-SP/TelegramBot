#!/usr/bin/env python3
"""
Setup script to configure localized bot names and descriptions.
Configures automatic language detection to display bot info in user's Telegram language.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_localized_bot_info():
    """Configure bot names and descriptions for different languages (Polish, Ukrainian, Russian)."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        # Localized bot information
        bot_info = {
            'en': {
                'name': 'Work in Poland',
                'description': 'We help you find work in Poland! Browse job offers, apply for positions and contact our recruitment team. Fast, convenient and professional.',
                'short_description': 'Find work in Poland - fast and convenient!'
            },
            'pl': {
                'name': 'Praca w Polsce',
                'description': 'Pomożemy znaleźć pracę w Polsce! Przeglądaj oferty pracy, aplikuj na stanowiska i skontaktuj się z naszym zespołem rekrutacyjnym. Szybko, wygodnie i profesjonalnie.',
                'short_description': 'Znajdź pracę w Polsce - szybko i wygodnie!'
            },
            'uk': {  # Ukrainian uses 'uk' in ISO 639-1
                'name': 'Робота в Польщі',
                'description': 'Допоможемо знайти роботу в Польщі! Переглядай вакансії, подавай заявки на посади та зв\'яжись з нашою командою рекрутерів. Швидко, зручно та професійно.',
                'short_description': 'Знайди роботу в Польщі — швидко та зручно!'
            },
            'ru': {
                'name': 'Работа в Польше',
                'description': 'Поможем найти работу в Польше! Просматривай вакансии, подавай заявки на должности и связывайся с нашей командой рекрутеров. Быстро, удобно и профессионально.',
                'short_description': 'Найди работу в Польше — быстро и удобно!'
            }
        }
        
        print("🌐 Setting up localized bot information...")
        
        # Set default (English/fallback) information
        await application.bot.set_my_name(name="Job in Poland", language_code="")
        await application.bot.set_my_description(
            description="We help you find work in Poland! Browse job offers, apply for positions and contact our recruitment team. Fast, convenient and professional.",
            language_code=""
        )
        await application.bot.set_my_short_description(
            short_description="Find work in Poland - fast and convenient!",
            language_code=""
        )
        print("✅ Set default (English) bot information")
        
        # Configure localized versions for each language
        for lang_code, info in bot_info.items():
            await application.bot.set_my_name(name=info['name'], language_code=lang_code)
            await application.bot.set_my_description(description=info['description'], language_code=lang_code)
            await application.bot.set_my_short_description(short_description=info['short_description'], language_code=lang_code)
            
            lang_names = {'en': 'English', 'pl': 'Polish', 'uk': 'Ukrainian', 'ru': 'Russian'}
            print(f"✅ Set {lang_names[lang_code]} bot information")
        
        print("\n🎉 Successfully set up localized bot names and descriptions!")
        print("\n📱 Language detection:")
        print("• English Telegram users will see: 'Work in Poland'")
        print("• Polish Telegram users will see: 'Praca w Polsce'")
        print("• Ukrainian Telegram users will see: 'Робота в Польщі'")
        print("• Russian Telegram users will see: 'Работа в Польше'")
        print("• Other language users will see: 'Work in Poland' (fallback)")
        print("\n🔄 Changes take effect immediately for new user interactions.")
        
    except Exception as e:
        print(f"❌ Error setting up localized bot info: {e}")
        logger.error(f"Error setting up localized bot info: {e}")

async def verify_localization():
    """Verify that localization is configured correctly for all languages."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        print("\n🔍 Verifying localization setup...")
        
        # Check different language versions
        languages = {
            '': 'Default (Fallback)',
            'en': 'English',
            'pl': 'Polish',
            'uk': 'Ukrainian', 
            'ru': 'Russian'
        }
        
        for lang_code, lang_name in languages.items():
            try:
                name_result = await application.bot.get_my_name(language_code=lang_code)
                desc_result = await application.bot.get_my_description(language_code=lang_code)
                short_desc_result = await application.bot.get_my_short_description(language_code=lang_code)
                
                print(f"\n📋 {lang_name} ({lang_code or 'default'}):")
                print(f"   Name: {name_result.name}")
                print(f"   Description: {desc_result.description[:50]}...")
                print(f"   Short Description: {short_desc_result.short_description}")
                
            except Exception as e:
                print(f"❌ Error checking {lang_name}: {e}")
        
        print("\n✅ Localization verification complete!")
        
    except Exception as e:
        print(f"❌ Error verifying localization: {e}")

async def main():
    """Main function to configure and verify localization."""
    await setup_localized_bot_info()
    await verify_localization()

if __name__ == "__main__":
    print("🚀 Setting up Telegram Bot Localization...")
    asyncio.run(main()) 