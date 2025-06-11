# RobotaVPolshchiBot - Multilingual Recruitment Telegram Bot

A production-ready multilingual Telegram bot designed to streamline the recruitment process for foreign workers in Poland. The bot facilitates job applications and candidate inquiries through an intuitive interface available in Polish, Ukrainian, and Russian languages.

## 🚀 Features

- **Multilingual Support**: Polish, Ukrainian, and Russian
- **Job Application Flow**: Complete form collection with validation
- **Contact Management**: Separate contact form handling
- **Google Sheets Integration**: Automatic data storage
- **Input Validation**: Comprehensive input sanitization and validation
- **Error Handling**: Production-grade error handling and logging
- **Health Monitoring**: Built-in health check endpoint

## 🛠 Tech Stack

- **Python 3.11+**
- **python-telegram-bot 21.9**: Modern async Telegram Bot API
- **Google Sheets API**: For data storage
- **gspread**: Google Sheets Python client
- **python-dotenv**: Environment variable management

## 📋 Prerequisites

1. **Telegram Bot Token**: Get from [@BotFather](https://t.me/botfather)
2. **Google Sheets API Credentials**: Service account with Sheets API access
3. **Google Spreadsheet**: Pre-created with "Applications" and "Contacts" sheets

## 🔧 Environment Variables

Create a `.env` file or set environment variables:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDENTIALS_BASE64=your_base64_encoded_service_account_json

# Optional (with defaults)
APPLICATIONS_SHEET_NAME=Applications
CONTACTS_SHEET_NAME=Contacts
```

### Getting Google Credentials Base64

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Convert to base64: `base64 -i credentials.json` (macOS/Linux) or `certutil -encode credentials.json temp.b64 && type temp.b64` (Windows)
4. Use the base64 string as `GOOGLE_CREDENTIALS_BASE64`

## 🚀 Deployment on Render

### Automatic Deployment

1. **Fork this repository** to your GitHub account

2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

3. **Configure Environment**:
   - Set environment variables in Render dashboard
   - Use the `render.yaml` configuration (automatic detection)

4. **Deploy**:
   - Render will automatically deploy using the `Procfile`
   - Monitor logs for successful startup

### Manual Configuration

If not using `render.yaml`:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Environment**: Python 3.11
- **Plan**: Starter (sufficient for most use cases)

## 📊 Google Sheets Setup

### Applications Sheet Columns:
1. Timestamp
2. User ID
3. Selected Job
4. Name
5. Country
6. Phone
7. Telegram Phone
8. Accommodation
9. City
10. Language

### Contacts Sheet Columns:
1. Timestamp
2. User ID
3. Name
4. Country
5. Phone
6. Telegram Phone
7. Accommodation
8. Availability
9. Language

## 🔍 Health Monitoring

The bot includes a health check endpoint at `/health` that returns:
- Google Sheets connection status
- Overall bot health
- Timestamp

## 🛡 Security Features

- **Input Validation**: Regex patterns for names, phones, etc.
- **Input Sanitization**: Removes potentially harmful characters
- **Error Handling**: Graceful degradation on failures
- **Logging**: Comprehensive logging for monitoring

## 📝 Available Commands

- `/start` - Initialize the bot and select language
- `/menu` - Return to main menu
- `/contact` - Show contact information
- `/language` - Change language
- `/cancel` - Cancel current operation

## 🔧 Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd TelegramBot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

## 📄 Log Files

The bot creates `bot.log` file for persistent logging. In production, monitor this file for:
- User interactions
- Error patterns
- Google Sheets connectivity issues
- Performance metrics

## 🚨 Error Handling

The bot includes multiple layers of error handling:
- **Input validation** with user-friendly error messages
- **Google Sheets failures** with graceful degradation
- **Telegram API errors** with retry logic
- **Uncaught exceptions** with user notifications

## 🤝 Support

For issues and questions:
- 📧 Email: rekrutacja@folga.com.pl
- 📞 Phone: +48 502 202 902
- 🌐 Website: folga.com.pl

## 📄 License

This project is proprietary software developed for Folga recruitment services.

---

**Built with ❤️ for efficient recruitment processes in Poland** 