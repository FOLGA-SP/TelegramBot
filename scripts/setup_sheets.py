#!/usr/bin/env python3
"""
Setup script to initialize Google Sheets with proper headers.
Run this once before starting the bot to create required worksheets.
"""

import os
import json
import base64
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Configuration from environment
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
APPLICATIONS_SHEET_NAME = os.getenv("APPLICATIONS_SHEET_NAME", "Applications")
CONTACTS_SHEET_NAME = os.getenv("CONTACTS_SHEET_NAME", "Contacts")

def get_google_credentials():
    """Load Google service account credentials from base64 environment variable."""
    google_creds_base64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
    if not google_creds_base64:
        raise Exception("GOOGLE_CREDENTIALS_BASE64 environment variable is required")
    
    try:
        # Decode base64 and parse JSON credentials
        creds_json = base64.b64decode(google_creds_base64).decode('utf-8')
        creds_info = json.loads(creds_json)
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        return Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception as e:
        raise Exception(f"Failed to load Google credentials: {e}")

def setup_google_sheets():
    """Initialize Google Sheets with proper headers for Applications and Contacts."""
    try:
        # Connect to Google Sheets
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        
        # Setup Applications sheet
        try:
            applications_sheet = sheet.worksheet(APPLICATIONS_SHEET_NAME)
            print(f"Found existing '{APPLICATIONS_SHEET_NAME}' sheet")
        except gspread.WorksheetNotFound:
            applications_sheet = sheet.add_worksheet(title=APPLICATIONS_SHEET_NAME, rows=1000, cols=10)
            print(f"Created '{APPLICATIONS_SHEET_NAME}' sheet")
        
        # Set Applications sheet headers
        applications_headers = [
            'Timestamp',
            'User ID',
            'Job Position',
            'Name',
            'Country',
            'Phone',
            'Telegram Phone',
            'Accommodation Needed',
            'Current City',
            'Language'
        ]
        
        # Add headers if missing or different
        try:
            existing_headers = applications_sheet.row_values(1)
            if not existing_headers or existing_headers != applications_headers:
                applications_sheet.insert_row(applications_headers, 1)
                print(f"Added headers to '{APPLICATIONS_SHEET_NAME}' sheet")
            else:
                print(f"Headers already exist in '{APPLICATIONS_SHEET_NAME}' sheet")
        except:
            applications_sheet.insert_row(applications_headers, 1)
            print(f"Added headers to '{APPLICATIONS_SHEET_NAME}' sheet")
        
        # Setup Contacts sheet
        try:
            contacts_sheet = sheet.worksheet(CONTACTS_SHEET_NAME)
            print(f"Found existing '{CONTACTS_SHEET_NAME}' sheet")
        except gspread.WorksheetNotFound:
            contacts_sheet = sheet.add_worksheet(title=CONTACTS_SHEET_NAME, rows=1000, cols=10)
            print(f"Created '{CONTACTS_SHEET_NAME}' sheet")
        
        # Set Contacts sheet headers
        contacts_headers = [
            'Timestamp',
            'User ID',
            'Name',
            'Country',
            'Phone',
            'Telegram Phone',
            'Accommodation Needed',
            'Availability',
            'Language'
        ]
        
        # Add headers if missing or different
        try:
            existing_headers = contacts_sheet.row_values(1)
            if not existing_headers or existing_headers != contacts_headers:
                contacts_sheet.insert_row(contacts_headers, 1)
                print(f"Added headers to '{CONTACTS_SHEET_NAME}' sheet")
            else:
                print(f"Headers already exist in '{CONTACTS_SHEET_NAME}' sheet")
        except:
            contacts_sheet.insert_row(contacts_headers, 1)
            print(f"Added headers to '{CONTACTS_SHEET_NAME}' sheet")
        
        print("\n✅ Google Sheets setup completed successfully!")
        print(f"📊 Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Google Sheets for Telegram Bot...")
    setup_google_sheets() 