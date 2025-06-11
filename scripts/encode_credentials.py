#!/usr/bin/env python3
"""
Utility script to encode Google credentials JSON file to base64.
Use this script to generate the GOOGLE_CREDENTIALS_BASE64 value for GitHub secrets.
"""

import base64
import json
import os

def encode_credentials_file(file_path="telgrambot-462311-79b418d99807.json"):
    """Encode Google credentials JSON file to base64."""
    try:
        if not os.path.exists(file_path):
            print(f"❌ Error: File '{file_path}' not found!")
            print("Make sure the Google credentials JSON file exists in the project root.")
            return None
        
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            json_content = file.read()
        
        # Validate it's valid JSON
        json.loads(json_content)
        
        # Encode to base64
        encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
        
        print("✅ Successfully encoded Google credentials to base64!")
        print("\n📝 Copy this value to your GitHub repository secrets:")
        print("Secret name: GOOGLE_CREDENTIALS_BASE64")
        print("Secret value:")
        print("-" * 50)
        print(encoded_content)
        print("-" * 50)
        
        # Save to a temporary file for easy copying
        with open('google_credentials_base64.txt', 'w') as f:
            f.write(encoded_content)
        
        print("\n💾 Also saved to 'google_credentials_base64.txt' for easy copying")
        print("\n🔒 Security reminder:")
        print("• Add google_credentials_base64.txt to .gitignore")
        print("• Delete the temporary file after copying to GitHub secrets")
        print("• Never commit the base64 encoded credentials to your repository")
        
        return encoded_content
        
    except json.JSONDecodeError:
        print(f"❌ Error: '{file_path}' is not a valid JSON file!")
        return None
    except Exception as e:
        print(f"❌ Error encoding credentials: {e}")
        return None

def test_decoding(encoded_content):
    """Test that the encoded content can be decoded properly."""
    try:
        # Decode base64
        decoded_content = base64.b64decode(encoded_content).decode('utf-8')
        
        # Parse JSON
        creds_info = json.loads(decoded_content)
        
        # Check for required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_info]
        
        if missing_fields:
            print(f"❌ Warning: Missing required fields: {missing_fields}")
            return False
        
        print("✅ Encoding test passed - credentials can be decoded properly!")
        return True
        
    except Exception as e:
        print(f"❌ Decoding test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Google Credentials Base64 Encoder")
    print("=" * 40)
    
    # Check if credentials file exists
    file_path = "telgrambot-462311-79b418d99807.json"
    if not os.path.exists(file_path):
        file_path = input("Enter path to Google credentials JSON file: ").strip()
    
    # Encode the credentials
    encoded = encode_credentials_file(file_path)
    
    if encoded:
        # Test the encoding
        print("\n🧪 Testing encoding...")
        test_decoding(encoded)
        
        print("\n📋 Next steps:")
        print("1. Go to your GitHub repository")
        print("2. Navigate to Settings → Secrets and variables → Actions")
        print("3. Click 'New repository secret'")
        print("4. Name: GOOGLE_CREDENTIALS_BASE64")
        print("5. Value: (paste the base64 string above)")
        print("6. Click 'Add secret'") 