import logging
import os
import json
import base64
import re
import asyncio
from typing import Optional
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "GOOGLE_SHEET_ID", 
    "GOOGLE_CREDENTIALS_BASE64"
]

def validate_environment():
    """Validate that all required environment variables are present."""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    logger.info("All required environment variables are present")

# Validate environment on startup
validate_environment()

# Configuration from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
APPLICATIONS_SHEET_NAME = os.getenv("APPLICATIONS_SHEET_NAME", "Applications")
CONTACTS_SHEET_NAME = os.getenv("CONTACTS_SHEET_NAME", "Contacts")

# Conversation states for the bot flow
LANGUAGE_SELECTION, MAIN_MENU, JOB_SELECTION, JOB_DESCRIPTION, JOB_APPLICATION, CONTACT_OPTION, CONTACT_FORM = range(7)

# Input validation patterns
PHONE_PATTERN = re.compile(r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$')
NAME_PATTERN = re.compile(r'^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻіїєІЇЄйцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ\s\-\'\.]{2,50}$')

# Global Google Sheets client (connection pooling)
google_client = None

# Translation dictionary
TRANSLATIONS = {
    'pl': {
        'welcome': '🇵🇱 Pomożemy znaleźć pracę w Polsce - szybko i wygodnie!',
        'choose_language': 'Wybierz język',
        'main_menu': 'Menu główne',
        'check_jobs': 'Sprawdź oferty pracy',
        'contact_us': 'Skontaktuj się z nami',
        'fill_form': 'Wypełnij formularz',
        'contact_info': 'Kontakt',
        'job_offers': 'Dostępne oferty pracy:',
        'name': 'Imię i Nazwisko',
        'country': 'Kraj pochodzenia',
        'phone': 'Telefon kontaktowy',
        'telegram_phone': 'Telefon kontaktowy Telegram',
        'accommodation': 'Czy potrzebujesz zakwaterowania? (Tak/Nie)',
        'current_city': 'W którym mieście obecnie przebywasz?',
        'availability': 'Od kiedy będziesz gotowy do nowej pracy?',
        'thank_you': '✅ Dziękujemy! Skontaktujemy się z Tobą wkrótce.',
        'error_occurred': '❌ Wystąpił błąd. Spróbuj ponownie lub skontaktuj się z nami.',
        'invalid_input': '❌ Nieprawidłowe dane. Spróbuj ponownie.',
        'invalid_phone': '❌ Nieprawidłowy numer telefonu. Wprowadź prawidłowy numer.',
        'invalid_name': '❌ Nieprawidłowe imię/nazwisko. Używaj tylko liter.',
        'contact_details': '''📞 W razie pytań możesz się z nami skontaktować:

📧 Email: rekrutacja@folga.com.pl
📞 Telefon: +48 502 202 902
🌐 Strona internetowa: folga.com.pl

Jesteśmy dostępni od poniedziałku do piątku, 8:00-17:00''',
        'jobs': [
            'Pracownik działu mięsnego w supermarkecie',
            'Pracownik w supermarkecie',
            'Kasjer do supermarketu',
            'Pracownik produkcji',
            'Brygadzista na produkcję mięsną'
        ],
        'apply_for_job': 'Aplikuj na to stanowisko',
        'back': 'Powrót',
        'cancel': 'Anuluj',
        'enter_name': 'Podaj swoje imię i nazwisko:',
        'enter_country': 'Podaj kraj pochodzenia:',
        'enter_phone': 'Podaj telefon kontaktowy:',
        'enter_telegram_phone': 'Podaj telefon kontaktowy Telegram:',
        'enter_accommodation': 'Czy potrzebujesz zakwaterowania? (Tak/Nie)',
        'enter_city': 'W którym mieście obecnie przebywasz?',
        'enter_availability': 'Od kiedy będziesz gotowy do nowej pracy?',
        'yes': 'Tak',
        'no': 'Nie'
    },
    'ua': {
        'welcome': '🇺🇦 Допоможемо знайти роботу в Польщі — швидко та зручно!',
        'choose_language': 'Виберіть мову',
        'main_menu': 'Головне меню',
        'check_jobs': 'Перевір вакансії',
        'contact_us': 'Зв\'яжись з нами',
        'fill_form': 'Заповнити анкету',
        'contact_info': 'Контакт',
        'job_offers': 'Доступні вакансії:',
        'name': 'Ім\'я та Прізвище',
        'country': 'Країна походження',
        'phone': 'Контактний номер телефону',
        'telegram_phone': 'Контактний номер у Telegram',
        'accommodation': 'Чи потребуєш житло? (Так/Ні)',
        'current_city': 'У якому місті зараз перебуваєш?',
        'availability': 'Від коли плануєш почати працювати?',
        'thank_you': '✅ Дякуємо! Ми зв\'яжемося з Вами найближчим часом.',
        'error_occurred': '❌ Виникла помилка. Спробуйте ще раз або зв\'яжіться з нами.',
        'invalid_input': '❌ Неправильні дані. Спробуйте ще раз.',
        'invalid_phone': '❌ Неправильний номер телефону. Введіть правильний номер.',
        'invalid_name': '❌ Неправильне ім\'я/прізвище. Використовуйте тільки літери.',
        'contact_details': '''📞 З питань можете з нами зв\'язатися:

📧 Email: rekrutacja@folga.com.pl
📞 Телефон: +48 502 202 902
🌐 Вебсайт: folga.com.pl

Ми доступні з понеділка по п\'ятницю, 8:00-17:00''',
        'jobs': [
            'Працівник м\'ясного відділу в супермаркеті',
            'Працівник супермаркету',
            'Касир до супермаркету',
            'Працівник виробництва',
            'Бригадир на м\'ясному виробництві'
        ],
        'apply_for_job': 'Подати заяву на цю посаду',
        'back': 'Назад',
        'cancel': 'Скасувати',
        'enter_name': 'Введіть своє ім\'я та прізвище:',
        'enter_country': 'Введіть країну походження:',
        'enter_phone': 'Введіть контактний номер телефону:',
        'enter_telegram_phone': 'Введіть контактний номер у Telegram:',
        'enter_accommodation': 'Чи потребуєш житло? (Так/Ні)',
        'enter_city': 'У якому місті зараз перебуваєш?',
        'enter_availability': 'Від коли плануєш почати працювати?',
        'yes': 'Так',
        'no': 'Ні'
    },
    'ru': {
        'welcome': '🇷🇺 Поможем вам найти работу в Польше — быстро и удобно!',
        'choose_language': 'Выберите язык',
        'main_menu': 'Главное меню',
        'check_jobs': 'Проверь вакансии',
        'contact_us': 'Свяжись с нами',
        'fill_form': 'Заполнить анкету',
        'contact_info': 'Контакты',
        'job_offers': 'Доступные вакансии:',
        'name': 'Имя и Фамилия',
        'country': 'Страна происхождения',
        'phone': 'Контактный номер телефона',
        'telegram_phone': 'Контактный номер Telegram',
        'accommodation': 'Нуждаетесь в жилье? (Да/Нет)',
        'current_city': 'В каком городе вы сейчас находитесь?',
        'availability': 'От когда планируете начать работать?',
        'thank_you': '✅ Спасибо! Мы свяжемся с вами в ближайшее время.',
        'error_occurred': '❌ Произошла ошибка. Попробуйте еще раз или свяжитесь с нами.',
        'invalid_input': '❌ Неправильные данные. Попробуйте еще раз.',
        'invalid_phone': '❌ Неправильный номер телефона. Введите правильный номер.',
        'invalid_name': '❌ Неправильное имя/фамилия. Используйте только буквы.',
        'contact_details': '''📞 По вопросам можете с нами связаться:

📧 Email: rekrutacja@folga.com.pl
📞 Телефон: +48 502 202 902
🌐 Сайт: folga.com.pl

Мы доступны с понедельника по пятницу, 8:00-17:00''',
        'jobs': [
            'Работник мясного отдела в супермаркете',
            'Работник супермаркета',
            'Кассир в супермаркет',
            'Работник производства',
            'Бригадир на мясном производстве'
        ],
        'apply_for_job': 'Подать заявку на эту должность',
        'back': 'Назад',
        'cancel': 'Отмена',
        'enter_name': 'Введите ваше имя и фамилию:',
        'enter_country': 'Введите страну происхождения:',
        'enter_phone': 'Введите контактный номер телефона:',
        'enter_telegram_phone': 'Введите контактный номер Telegram:',
        'enter_accommodation': 'Нуждаетесь в жилье? (Да/Нет)',
        'enter_city': 'В каком городе вы сейчас находитесь?',
        'enter_availability': 'От когда планируете начать работать?',
        'yes': 'Да',
        'no': 'Нет'
    }
}

def validate_input(input_type: str, value: str) -> bool:
    """Validate user input based on type."""
    if not value or len(value.strip()) == 0:
        return False
    
    value = value.strip()
    
    if input_type == 'name':
        # The regex already enforces a length of 2 to 50 characters.
        return NAME_PATTERN.match(value) is not None
    elif input_type == 'phone':
        return PHONE_PATTERN.match(value) is not None
    elif input_type == 'country':
        return 2 <= len(value) <= 50
    elif input_type == 'city':
        return 2 <= len(value) <= 50
    elif input_type == 'accommodation':
        return value.lower() in ['tak', 'nie', 'так', 'ні', 'да', 'нет', 'yes', 'no']
    elif input_type == 'availability':
        return 2 <= len(value) <= 100
    
    return True

def sanitize_input(value: str) -> str:
    """Sanitize user input for safe storage."""
    if not value:
        return ""
    
    # Remove any potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', value.strip())
    return sanitized[:500]  # Limit length

# Google Sheets integration with connection pooling
async def get_google_credentials():
    """Load Google service account credentials from base64 environment variable."""
    try:
        google_creds_base64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if not google_creds_base64:
            raise Exception("GOOGLE_CREDENTIALS_BASE64 environment variable is required")
        
        # Decode base64 and parse JSON credentials
        creds_json = base64.b64decode(google_creds_base64).decode('utf-8')
        creds_info = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        logger.error(f"Failed to load Google credentials: {e}")
        raise

async def setup_google_sheets() -> Optional[gspread.Spreadsheet]:
    """Connect to Google Sheets and return the workbook with connection pooling."""
    global google_client
    
    try:
        if google_client is None:
            creds = await get_google_credentials()
            google_client = gspread.authorize(creds)
            logger.info("Google Sheets client initialized")
        
        return google_client.open_by_key(SHEET_ID)
    except Exception as e:
        logger.error(f"Error setting up Google Sheets: {e}")
        google_client = None  # Reset client on error
        return None

# Job description loading functions
def format_job_description_for_telegram(content: str, language: str) -> str:
    """Convert markdown job description to Telegram-friendly format with emojis."""
    try:
        lines = content.split('\n')
        formatted_lines = []
        
        # Emoji mappings for different job types
        job_emojis = {
            'pl': {
                'Pracownik działu mięsnego w supermarkecie': '🥩',
                'Pracownik w supermarkecie': '🏪',
                'Kasjer do supermarketu': '🛒',
                'Brygadzista na produkcję mięsną': '👷‍♂️',
                'Pracownik produkcji': '🏭'
            },
            'ua': {
                'Працівник м\'ясного відділу в супермаркеті': '🥩',
                'Працівник супермаркету': '🏪',
                'Касир до супермаркету': '🛒',
                'Бригадир на м\'ясному виробництві': '👷‍♂️',
                'Працівник виробництва': '🏭'
            },
            'ru': {
                'Работник мясного отдела в супермаркете': '🥩',
                'Работник супермаркета': '🏪',
                'Кассир в супермаркет': '🛒',
                'Бригадир на мясном производстве': '👷‍♂️',
                'Работник производства': '🏭'
            },
            'en': {
                'Meat Department Worker in Supermarket': '🥩',
                'Supermarket Worker': '🏪',
                'Supermarket Cashier': '🛒',
                'Foreman in Meat Production': '👷‍♂️',
                'Production Worker': '🏭'
            }
        }
        
        # Section emoji mappings
        section_emojis = {
            'pl': {
                'Co dla nas jest ważne': '⚡',
                'Co możemy Ci zaoferować': '💰',
                'Co możemy Tobie zaoferować': '💰',
                'Zapraszamy do udziału w rekrutacji': '📝',
                'Obowiązki Brygadzisty': '📋'
            },
            'ua': {
                'Що для нас важливо': '⚡',
                'Що ми можемо Вам запропонувати': '💰',
                'Запрошуємо до участі в рекрутації': '📝',
                'Обов\'язки Бригадира': '📋'
            },
            'ru': {
                'Что для нас важно': '⚡',
                'Что мы можем Вам предложить': '💰',
                'Приглашаем к участию в рекрутинге': '📝',
                'Обязанности Бригадира': '📋'
            },
            'en': {
                'What is important to us': '⚡',
                'What we can offer you': '💰',
                'We invite you to participate in recruitment': '📝',
                'Foreman Duties': '📋'
            }
        }
        
        for line in lines:
            # Handle main job titles (# Title)
            if line.startswith('# '):
                title = line[2:].strip()
                emoji = job_emojis.get(language, {}).get(title, '💼')
                formatted_lines.append(f"{emoji} *{title}*")
                formatted_lines.append("")  # Add spacing
                
            # Handle section headers (## Section)
            elif line.startswith('## '):
                section = line[3:].strip()
                emoji = section_emojis.get(language, {}).get(section, '▫️')
                formatted_lines.append(f"{emoji} *{section}*")
                formatted_lines.append("")  # Add spacing
                
            # Handle horizontal rules (---)
            elif line.strip() == '---':
                formatted_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                formatted_lines.append("")  # Add spacing
                
            # Handle main bullet points
            elif line.startswith('- '):
                bullet_text = line[2:].strip()
                formatted_lines.append(f"• {bullet_text}")
                
            # Handle sub-bullet points (indented)
            elif line.startswith('  - '):
                sub_bullet_text = line[4:].strip()
                formatted_lines.append(f"    ▪️ {sub_bullet_text}")
                
            # Handle regular lines
            elif line.strip():
                formatted_lines.append(line)
                
            # Handle empty lines
            else:
                formatted_lines.append("")
        
        # Join lines and clean up multiple consecutive empty lines
        result = '\n'.join(formatted_lines)
        
        # Replace multiple consecutive newlines with maximum 2
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Add some final formatting touches
        result = result.strip()
        
        return result
        
    except Exception as e:
        logger.error(f"Error formatting job description: {e}")
        return content  # Return original content if formatting fails

async def load_job_description(job_title: str, language: str) -> Optional[str]:
    """Load job description from markdown file based on job title and language."""
    try:
        # Map languages to file suffixes
        lang_map = {
            'pl': 'pl',
            'ua': 'uk', 
            'ru': 'ru',
            'en': 'en'
        }
        
        # Map job titles to markdown section headers
        job_mapping = {
            'pl': {
                'Pracownik działu mięsnego w supermarkecie': 'Pracownik działu mięsnego w supermarkecie',
                'Pracownik w supermarkecie': 'Pracownik w supermarkecie',
                'Kasjer do supermarketu': 'Kasjer do supermarketu',
                'Pracownik produkcji': 'Pracownik produkcji',
                'Brygadzista na produkcję mięsną': 'Brygadzista na produkcję mięsną'
            },
            'ua': {
                'Працівник м\'ясного відділу в супермаркеті': 'Працівник м\'ясного відділу в супермаркеті',
                'Працівник супермаркету': 'Працівник супермаркету',
                'Касир до супермаркету': 'Касир до супермаркету',
                'Працівник виробництва': 'Працівник виробництва',
                'Бригадир на м\'ясному виробництві': 'Бригадир на м\'ясному виробництві'
            },
            'ru': {
                'Работник мясного отдела в супермаркете': 'Работник мясного отдела в супермаркете',
                'Работник супермаркета': 'Работник супермаркета',
                'Кассир в супермаркет': 'Кассир в супермаркет',
                'Работник производства': 'Работник производства',
                'Бригадир на мясном производстве': 'Бригадир на мясном производстве'
            }
        }
        
        file_suffix = lang_map.get(language, 'pl')
        file_path = f"JobDescriptions/Job_descriptions_{file_suffix}.md"
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Job description file not found: {file_path}")
            return None
        
        # Get the section title for the job
        section_title = job_mapping.get(language, {}).get(job_title)
        if not section_title:
            logger.error(f"No mapping found for job '{job_title}' in language '{language}'")
            return None
        
        # Read and parse the markdown file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the section for this job
        sections = content.split('\n# ')
        
        for i, section in enumerate(sections):
            if i == 0:
                # First section might not start with \n#
                section_header = section.split('\n')[0].strip()
                if section_header.startswith('# '):
                    section_header = section_header[2:]
            else:
                section_header = section.split('\n')[0].strip()
            
            if section_header == section_title:
                # Found the section - clean it up and return
                if i == 0:
                    job_content = section
                else:
                    job_content = '# ' + section
                
                # Remove any following sections (stop at next #)
                lines = job_content.split('\n')
                final_lines = []
                for j, line in enumerate(lines):
                    if j > 0 and line.startswith('# ') and line.strip() != f'# {section_title}':
                        break
                    final_lines.append(line)
                
                job_content = '\n'.join(final_lines).strip()
                # Format the content for Telegram display
                return format_job_description_for_telegram(job_content, language)
        
        logger.error(f"Job section '{section_title}' not found in file {file_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading job description: {e}")
        return None

# Helper functions
def get_text(lang: str, key: str) -> str:
    """Get translated text with fallback."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['pl']).get(key, key)

def create_keyboard(buttons, lang):
    """Create keyboard with proper error handling."""
    try:
        keyboard = []
        for button in buttons:
            if isinstance(button, list):
                keyboard.append([KeyboardButton(get_text(lang, btn)) for btn in button])
            else:
                keyboard.append([KeyboardButton(get_text(lang, button))])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    except Exception as e:
        logger.error(f"Error creating keyboard: {e}")
        # Return basic keyboard as fallback
        return ReplyKeyboardMarkup([[KeyboardButton("Menu")]], resize_keyboard=True)

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error_msg: str = None) -> int:
    """Handle errors gracefully and return to main menu."""
    try:
        lang = context.user_data.get('language', 'pl')
        message = error_msg or get_text(lang, 'error_occurred')
        
        await update.message.reply_text(message)
        logger.error(f"Error handled for user {update.effective_user.id}: {error_msg}")
        
        return await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
        return MAIN_MENU

# Bot handlers with improved error handling
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation. If language is set, show main menu, otherwise ask for language."""
    try:
        lang = context.user_data.get('language')
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        if lang:
            logger.info(f"User {user_id} ({username}) restarted with language '{lang}'. Returning to main menu.")
            # Reset form state but keep language
            for key in ['form_data', 'form_step', 'selected_job']:
                context.user_data.pop(key, None)
            return await show_main_menu(update, context)
        
        # New user or language not set
        logger.info(f"User {user_id} ({username}) started the bot. Asking for language.")
        
        keyboard = [
            [KeyboardButton("🇵🇱 Polski"), KeyboardButton("🇺🇦 Українська"), KeyboardButton("🇷🇺 Русский")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🌍 Wybierz język / Виберіть мову / Выберите язык",
            reply_markup=reply_markup
        )
        return LANGUAGE_SELECTION
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        return await handle_error(update, context)

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection and show main menu."""
    try:
        lang_map = {
            "🇵🇱 Polski": "pl", 
            "Polski": "pl",
            "🇺🇦 Українська": "ua", 
            "Українська": "ua",
            "🇷🇺 Русский": "ru",
            "Русский": "ru"
        }
        selected_lang = lang_map.get(update.message.text, "pl")
        context.user_data['language'] = selected_lang
        
        user_id = update.effective_user.id
        logger.info(f"User {user_id} selected language: {selected_lang}")
        
        keyboard = [
            [get_text(selected_lang, 'check_jobs')],
            [get_text(selected_lang, 'contact_us')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_text = get_text(selected_lang, 'welcome')
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in language_selected: {e}")
        return await handle_error(update, context)

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu selection."""
    try:
        lang = context.user_data.get('language', 'pl')
        text = update.message.text
        
        if text == get_text(lang, 'check_jobs'):
            # Show job offers
            jobs = get_text(lang, 'jobs')
            keyboard = [[job] for job in jobs]
            keyboard.append([get_text(lang, 'back')])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                get_text(lang, 'job_offers'),
                reply_markup=reply_markup
            )
            return JOB_SELECTION
        
        elif text == get_text(lang, 'contact_us'):
            # Show contact options
            keyboard = [
                [get_text(lang, 'fill_form')],
                [get_text(lang, 'contact_info')],
                [get_text(lang, 'back')]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                get_text(lang, 'contact_us'),
                reply_markup=reply_markup
            )
            return CONTACT_OPTION
        
        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in main_menu_handler: {e}")
        return await handle_error(update, context)

async def job_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle job selection and show job description."""
    try:
        lang = context.user_data.get('language', 'pl')
        text = update.message.text
        
        if text == get_text(lang, 'back'):
            return await show_main_menu(update, context)
        
        # Check if it's a valid job
        jobs = get_text(lang, 'jobs')
        if text in jobs:
            context.user_data['selected_job'] = text
            
            # Load job description
            job_description = await load_job_description(text, lang)
            
            if job_description:
                # Show job description with apply button
                keyboard = [
                    [get_text(lang, 'apply_for_job')],
                    [get_text(lang, 'back')]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    job_description,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return JOB_DESCRIPTION
            else:
                # Fallback if job description not found
                await update.message.reply_text(
                    f"❌ {get_text(lang, 'error_occurred')}"
                )
                return JOB_SELECTION
        
        return JOB_SELECTION
    except Exception as e:
        logger.error(f"Error in job_selected: {e}")
        return await handle_error(update, context)

async def job_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle job description actions - apply or go back."""
    try:
        lang = context.user_data.get('language', 'pl')
        text = update.message.text
        
        if text == get_text(lang, 'back'):
            # Go back to job selection
            jobs = get_text(lang, 'jobs')
            keyboard = [[job] for job in jobs]
            keyboard.append([get_text(lang, 'back')])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                get_text(lang, 'job_offers'),
                reply_markup=reply_markup
            )
            return JOB_SELECTION
        
        elif text == get_text(lang, 'apply_for_job'):
            # Start application form
            context.user_data['form_data'] = {}
            context.user_data['form_step'] = 'name'
            context.user_data['user_id'] = update.effective_user.id
            
            keyboard = [[get_text(lang, 'cancel')]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                get_text(lang, 'enter_name'),
                reply_markup=reply_markup
            )
            return JOB_APPLICATION
        
        return JOB_DESCRIPTION
    except Exception as e:
        logger.error(f"Error in job_description_handler: {e}")
        return await handle_error(update, context)

async def job_application_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle job application form steps with input validation."""
    try:
        lang = context.user_data.get('language', 'pl')
        text = update.message.text
        
        if text == get_text(lang, 'cancel'):
            return await show_main_menu(update, context)
        
        form_step = context.user_data.get('form_step')
        form_data = context.user_data.get('form_data', {})
        
        if form_step == 'name':
            if not validate_input('name', text):
                await update.message.reply_text(get_text(lang, 'invalid_name'))
                return JOB_APPLICATION
            
            form_data['name'] = sanitize_input(text)
            context.user_data['form_step'] = 'country'
            await update.message.reply_text(get_text(lang, 'enter_country'))
        
        elif form_step == 'country':
            if not validate_input('country', text):
                await update.message.reply_text(get_text(lang, 'invalid_input'))
                return JOB_APPLICATION
            
            form_data['country'] = sanitize_input(text)
            context.user_data['form_step'] = 'phone'
            await update.message.reply_text(get_text(lang, 'enter_phone'))
        
        elif form_step == 'phone':
            if not validate_input('phone', text):
                await update.message.reply_text(get_text(lang, 'invalid_phone'))
                return JOB_APPLICATION
            
            form_data['phone'] = sanitize_input(text)
            context.user_data['form_step'] = 'telegram_phone'
            await update.message.reply_text(get_text(lang, 'enter_telegram_phone'))
        
        elif form_step == 'telegram_phone':
            if not validate_input('phone', text):
                await update.message.reply_text(get_text(lang, 'invalid_phone'))
                return JOB_APPLICATION
            
            form_data['telegram_phone'] = sanitize_input(text)
            context.user_data['form_step'] = 'accommodation'
            
            keyboard = [[get_text(lang, 'yes'), get_text(lang, 'no')]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                get_text(lang, 'enter_accommodation'),
                reply_markup=reply_markup
            )
        
        elif form_step == 'accommodation':
            if not validate_input('accommodation', text):
                await update.message.reply_text(get_text(lang, 'invalid_input'))
                return JOB_APPLICATION
            
            form_data['accommodation'] = sanitize_input(text)
            context.user_data['form_step'] = 'city'
            
            keyboard = [[get_text(lang, 'cancel')]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                get_text(lang, 'enter_city'),
                reply_markup=reply_markup
            )
        
        elif form_step == 'city':
            if not validate_input('city', text):
                await update.message.reply_text(get_text(lang, 'invalid_input'))
                return JOB_APPLICATION
            
            form_data['city'] = sanitize_input(text)
            context.user_data['form_data'] = form_data
            
            # Save to Google Sheets
            success = await save_job_application(context.user_data)
            
            if success:
                await update.message.reply_text(
                    get_text(lang, 'thank_you'),
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    get_text(lang, 'error_occurred'),
                    reply_markup=ReplyKeyboardRemove()
                )
            
            return await show_main_menu(update, context)
        
        context.user_data['form_data'] = form_data
        return JOB_APPLICATION
    except Exception as e:
        logger.error(f"Error in job_application_handler: {e}")
        return await handle_error(update, context)

async def contact_option_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact options."""
    lang = context.user_data.get('language', 'pl')
    text = update.message.text
    
    if text == get_text(lang, 'back'):
        return await show_main_menu(update, context)
    
    elif text == get_text(lang, 'fill_form'):
        context.user_data['form_data'] = {}
        context.user_data['form_step'] = 'name'
        context.user_data['user_id'] = update.effective_user.id
        
        keyboard = [[get_text(lang, 'cancel')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            get_text(lang, 'enter_name'),
            reply_markup=reply_markup
        )
        return CONTACT_FORM
    
    elif text == get_text(lang, 'contact_info'):
        keyboard = [[get_text(lang, 'back')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            get_text(lang, 'contact_details'),
            reply_markup=reply_markup
        )
        return CONTACT_OPTION
    
    return CONTACT_OPTION

async def contact_form_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact form steps."""
    lang = context.user_data.get('language', 'pl')
    text = update.message.text
    
    if text == get_text(lang, 'cancel'):
        return await show_main_menu(update, context)
    
    form_step = context.user_data.get('form_step')
    form_data = context.user_data.get('form_data', {})
    
    if form_step == 'name':
        if not validate_input('name', text):
            await update.message.reply_text(get_text(lang, 'invalid_name'))
            return CONTACT_FORM
        form_data['name'] = sanitize_input(text)
        context.user_data['form_step'] = 'country'
        await update.message.reply_text(get_text(lang, 'enter_country'))
    
    elif form_step == 'country':
        if not validate_input('country', text):
            await update.message.reply_text(get_text(lang, 'invalid_input'))
            return CONTACT_FORM
        form_data['country'] = sanitize_input(text)
        context.user_data['form_step'] = 'phone'
        await update.message.reply_text(get_text(lang, 'enter_phone'))
    
    elif form_step == 'phone':
        if not validate_input('phone', text):
            await update.message.reply_text(get_text(lang, 'invalid_phone'))
            return CONTACT_FORM
        form_data['phone'] = sanitize_input(text)
        context.user_data['form_step'] = 'telegram_phone'
        await update.message.reply_text(get_text(lang, 'enter_telegram_phone'))
    
    elif form_step == 'telegram_phone':
        if not validate_input('phone', text):
            await update.message.reply_text(get_text(lang, 'invalid_phone'))
            return CONTACT_FORM
        form_data['telegram_phone'] = sanitize_input(text)
        context.user_data['form_step'] = 'accommodation'
        
        keyboard = [[get_text(lang, 'yes'), get_text(lang, 'no')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            get_text(lang, 'enter_accommodation'),
            reply_markup=reply_markup
        )
    
    elif form_step == 'accommodation':
        if not validate_input('accommodation', text):
            await update.message.reply_text(get_text(lang, 'invalid_input'))
            return CONTACT_FORM
        form_data['accommodation'] = sanitize_input(text)
        context.user_data['form_step'] = 'availability'
        
        keyboard = [[get_text(lang, 'cancel')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            get_text(lang, 'enter_availability'),
            reply_markup=reply_markup
        )
    
    elif form_step == 'availability':
        if not validate_input('availability', text):
            await update.message.reply_text(get_text(lang, 'invalid_input'))
            return CONTACT_FORM
        form_data['availability'] = sanitize_input(text)
        context.user_data['form_data'] = form_data
        
        # Save to Google Sheets
        success = await save_contact_form(context.user_data)
        
        if success:
            await update.message.reply_text(
                get_text(lang, 'thank_you'),
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                get_text(lang, 'error_occurred'),
                reply_markup=ReplyKeyboardRemove()
            )
        return await show_main_menu(update, context)
    
    context.user_data['form_data'] = form_data
    return CONTACT_FORM

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the main menu."""
    lang = context.user_data.get('language', 'pl')
    
    keyboard = [
        [get_text(lang, 'check_jobs')],
        [get_text(lang, 'contact_us')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        get_text(lang, 'main_menu'),
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def save_job_application(user_data) -> bool:
    """Save job application data to Google Sheets Applications worksheet."""
    try:
        sheet = await setup_google_sheets()
        if not sheet:
            logger.error("Could not connect to Google Sheets")
            return False
        
        worksheet = sheet.worksheet(APPLICATIONS_SHEET_NAME)
        
        # Prepare row data for insertion
        form_data = user_data.get('form_data', {})
        user_id = user_data.get('user_id', 'Unknown')
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            str(user_id),
            user_data.get('selected_job', ''),
            form_data.get('name', ''),
            form_data.get('country', ''),
            form_data.get('phone', ''),
            form_data.get('telegram_phone', ''),
            form_data.get('accommodation', ''),
            form_data.get('city', ''),
            user_data.get('language', 'pl')
        ]
        
        worksheet.append_row(row)
        logger.info(f"Job application saved successfully for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving job application: {e}")
        return False

async def save_contact_form(user_data) -> bool:
    """Save contact form data to Google Sheets Contacts worksheet."""
    try:
        sheet = await setup_google_sheets()
        if not sheet:
            logger.error("Could not connect to Google Sheets")
            return False
        
        worksheet = sheet.worksheet(CONTACTS_SHEET_NAME)
        
        # Prepare row data for insertion
        form_data = user_data.get('form_data', {})
        user_id = user_data.get('user_id', 'Unknown')
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            str(user_id),
            form_data.get('name', ''),
            form_data.get('country', ''),
            form_data.get('phone', ''),
            form_data.get('telegram_phone', ''),
            form_data.get('accommodation', ''),
            form_data.get('availability', ''),
            user_data.get('language', 'pl')
        ]
        
        worksheet.append_row(row)
        logger.info(f"Contact form saved successfully for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving contact form: {e}")
        return False

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /menu command - go to main menu."""
    lang = context.user_data.get('language', 'pl')
    
    # If no language selected yet, start language selection
    if not lang:
        return await start(update, context)
    
    return await show_main_menu(update, context)

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /contact command - show contact information."""
    lang = context.user_data.get('language', 'pl')
    
    # If no language selected yet, start language selection
    if not lang:
        return await start(update, context)
    
    await update.message.reply_text(get_text(lang, 'contact_details'))
    
    # Return to current state or main menu
    return await show_main_menu(update, context)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /language command - allow user to change language."""
    keyboard = [
        [KeyboardButton("🇵🇱 Polski"), KeyboardButton("🇺🇦 Українська"), KeyboardButton("🇷🇺 Русский")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🌍 Wybierz język / Виберіть мову / Выберите язык",
        reply_markup=reply_markup
    )
    return LANGUAGE_SELECTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation and return to main menu."""
    lang = context.user_data.get('language', 'pl')
    
    # Clear any form data
    context.user_data.pop('form_data', None)
    context.user_data.pop('form_step', None)
    context.user_data.pop('selected_job', None)
    
    # If no language selected yet, start language selection
    if not lang:
        return await start(update, context)
    
    # Return to main menu
    return await show_main_menu(update, context)

async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test Google Sheets connection
        sheet = await setup_google_sheets()
        if sheet:
            return {"status": "healthy", "google_sheets": "connected", "timestamp": datetime.now().isoformat()}
        else:
            return {"status": "degraded", "google_sheets": "disconnected", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}

async def startup_checks():
    """Perform startup checks and initialization."""
    logger.info("🚀 Starting RobotaVPolshchiBot...")
    
    # Validate environment
    try:
        validate_environment()
        logger.info("✅ Environment validation passed")
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False
    
    # Test Google Sheets connection
    try:
        sheet = await setup_google_sheets()
        if sheet:
            logger.info("✅ Google Sheets connection successful")
        else:
            logger.warning("⚠️ Google Sheets connection failed - bot will continue but data won't be saved")
    except Exception as e:
        logger.error(f"❌ Google Sheets connection error: {e}")
        logger.warning("⚠️ Continuing without Google Sheets - data won't be saved")
    
    # Test Telegram token
    try:
        from telegram import Bot
        bot = Bot(TOKEN)
        bot_info = await bot.get_me()
        logger.info(f"✅ Telegram bot connected: @{bot_info.username}")
    except Exception as e:
        logger.error(f"❌ Telegram bot connection failed: {e}")
        return False
    
    return True

async def main() -> None:
    """Initialize and start the Telegram bot with comprehensive error handling."""
    application = None
    try:
        # Run startup checks
        if not await startup_checks():
            logger.error("❌ Startup checks failed. Exiting.")
            return
        
        # Create the Application
        application = Application.builder().token(TOKEN).build()
        
        # Configure conversation handler with all states and commands
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CommandHandler('menu', menu_command),
                CommandHandler('language', language_command)
            ],
            states={
                LANGUAGE_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, language_selected),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                MAIN_MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                JOB_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, job_selected),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                JOB_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, job_description_handler),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                JOB_APPLICATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, job_application_handler),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                CONTACT_OPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, contact_option_handler),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
                CONTACT_FORM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, contact_form_handler),
                    CommandHandler('start', start),
                    CommandHandler('menu', menu_command),
                    CommandHandler('contact', contact_command),
                    CommandHandler('language', language_command)
                ],
            },
            fallbacks=[
                CommandHandler('start', start),
                CommandHandler('cancel', cancel),
                CommandHandler('contact', contact_command),
                CommandHandler('language', language_command)
            ],
        )
        
        application.add_handler(conv_handler)
        
        # Add error handler for uncaught exceptions
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Log the error and send a telegram message to notify the developer."""
            logger.error(f"Exception while handling an update: {context.error}")
            
            if update and hasattr(update, 'effective_user') and update.effective_user:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text="Wystąpił nieoczekiwany błąd. Spróbuj ponownie za chwilę."
                    )
                except Exception as e:
                    logger.error(f"Failed to send error message to user: {e}")
        
        application.add_error_handler(error_handler)
        
        logger.info("🤖 Bot is starting polling...")
        
        # Initialize and start the application manually for proper async handling
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=1.0,
            timeout=10
        )
        
        # Keep the bot running until interrupted
        await asyncio.Future()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error in main: {e}")
        raise
    finally:
        # Ensure proper cleanup
        if application:
            try:
                logger.info("🔄 Shutting down bot...")
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("✅ Bot shutdown complete")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

if __name__ == '__main__':
    asyncio.run(main()) 