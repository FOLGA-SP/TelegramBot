# Job Descriptions for RobotaVPolshchiBot

This directory contains job descriptions for the Telegram recruitment bot in multiple languages. The descriptions are automatically loaded and beautifully formatted for display in Telegram chats.

## 📁 File Structure

```
JobDescriptions/
├── Job_descriptions_pl.md    # Polish descriptions
├── Job_descriptions_uk.md    # Ukrainian descriptions  
├── Job_descriptions_ru.md    # Russian descriptions
├── Job_descriptions_en.md    # English descriptions
└── README.md                 # This documentation file
```

## 🔧 How It Works

### 1. **File Loading**
- Bot automatically reads markdown files based on user's language selection
- File mapping: `pl` → `_pl.md`, `ua` → `_uk.md`, `ru` → `_ru.md`, `en` → `_en.md`
- Each file contains multiple job descriptions in markdown format

### 2. **Job Mapping**
The bot maps job titles from user interface to markdown sections:

| Language | Bot Job Title | Markdown Section |
|----------|---------------|------------------|
| **Polish** | `Pracownik działu mięsnego w supermarkecie` | `# Pracownik działu mięsnego w supermarkecie` |
| **Polish** | `Pracownik w supermarkecie` | `# Pracownik w supermarkecie` |
| **Polish** | `Kasjer do supermarketu` | `# Kasjer do supermarketu` |
| **Polish** | `Pracownik produkcji` | `# Pracownik produkcji` |
| **Polish** | `Brygadzista na produkcję mięsną` | `# Brygadzista na produkcję mięsną` |

*Similar mappings exist for Ukrainian, Russian, and English versions.*

### 3. **Automatic Formatting**
Raw markdown is converted to Telegram-friendly format with:
- **Emojis** for job titles and sections
- **Bullet points** (`•` instead of `-`)
- **Sub-bullets** (`▪️` for indented items)
- **Decorative lines** (`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`)
- **Proper spacing** and text formatting

## 🎨 Formatting Rules

### Job Title Emojis
```
🥩 Meat Department Worker
🏪 Supermarket Worker  
🛒 Cashier
👷‍♂️ Foreman
🏭 Production Worker
```

### Section Emojis
```
⚡ Requirements/What's important
💰 Salary/What we offer
📝 Recruitment invitation
📋 Job duties/responsibilities
```

### Markdown Structure
Each job description should follow this structure:

```markdown
# Job Title

## Section Title

- **Bold text** for important points
- Regular bullet points
  - Sub-bullet points (indented with 2 spaces)
- **Bold items:** with descriptions

---

## Next Section Title

- More content...
```

## ✏️ How to Modify Existing Descriptions

### 1. **Edit Content**
- Open the appropriate language file (e.g., `Job_descriptions_pl.md`)
- Find the job section you want to modify
- Edit the content while maintaining the markdown structure
- Keep the job title exactly as it appears in the bot's job mapping

### 2. **Maintain Structure**
- Keep `# Job Title` format for main titles
- Keep `## Section Title` format for sections
- Use `---` for section separators
- Use proper bullet point indentation

### 3. **Test Changes**
- Restart the bot to reload the files
- Test the specific job description in Telegram
- Verify formatting looks correct

## ➕ How to Add New Job Descriptions

### 1. **Add to Markdown Files**
Add the new job description to **ALL** language files:

```markdown
# New Job Title

## What is important to us
- Job requirements...

---

## What we can offer you
- Salary and benefits...

---

## We invite you to participate in recruitment
- Application process...
```

### 2. **Update Bot Configuration**
In `bot.py`, add the new job to three places:

#### A. Translation Dictionary
```python
'jobs': [
    'Existing Job 1',
    'Existing Job 2',
    'New Job Title',  # Add here
    'Existing Job 3'
]
```

#### B. Job Mapping
```python
job_mapping = {
    'pl': {
        'New Job Title': 'New Job Title',  # Add here
        # ... existing mappings
    },
    'ua': {
        'Ukrainian Job Title': 'Ukrainian Job Title',  # Add here
        # ... existing mappings
    },
    # ... other languages
}
```

#### C. Job Emojis (Optional)
```python
job_emojis = {
    'pl': {
        'New Job Title': '🆕',  # Choose appropriate emoji
        # ... existing emojis
    },
    # ... other languages
}
```

### 3. **Restart Bot**
- Stop the bot
- Start the bot again to load new configuration
- Test the new job description

## 🌍 Language Support

### Current Languages
- **Polish** (`pl`) - Primary language
- **Ukrainian** (`ua`) - Maps to `_uk.md` file
- **Russian** (`ru`) - Full support
- **English** (`en`) - Full support

### Adding New Languages

1. **Create new markdown file**: `Job_descriptions_[lang].md`
2. **Update language mapping** in `bot.py`:
   ```python
   lang_map = {
       'pl': 'pl',
       'ua': 'uk',
       'ru': 'ru',
       'en': 'en',
       'new_lang': 'new_lang'  # Add here
   }
   ```
3. **Add translations** to job mappings and emoji mappings
4. **Add language option** to bot's language selection

## 🔍 Troubleshooting

### Job Description Not Loading
1. **Check file name** - Must match `Job_descriptions_[lang].md` pattern
2. **Check job title** - Must exactly match the mapping in `bot.py`
3. **Check markdown syntax** - Ensure proper `# Title` format
4. **Check file encoding** - Must be UTF-8

### Formatting Issues
1. **Emoji not showing** - Check if emoji mapping exists in `bot.py`
2. **Wrong bullets** - Ensure proper indentation (2 spaces for sub-bullets)
3. **Missing sections** - Check if `---` separators are present

### Bot Errors
1. **Check logs** - Bot logs errors when loading descriptions
2. **Validate markdown** - Ensure no syntax errors in files
3. **Restart bot** - Changes require bot restart

## 📝 Best Practices

1. **Keep consistency** across all language versions
2. **Use descriptive section headers** that match emoji mappings
3. **Test all languages** when making changes
4. **Backup files** before major changes
5. **Use proper markdown syntax** for best formatting
6. **Keep job titles short** for better mobile display

## 🔧 Technical Details

### File Processing
- Files are read with UTF-8 encoding
- Content is parsed by splitting on `\n# ` (newline + heading)
- Each job section is extracted individually
- Formatting is applied line by line

### Error Handling
- Missing files fall back to Polish version
- Invalid job mappings return error message
- Formatting errors return original content
- All errors are logged for debugging

---