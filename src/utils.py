from fastapi import Form
import re
import csv
import json
from datetime import datetime
import pandas as pd
import os
from src.config import LEADS_FILE,LOG_DIR


def save_lead_to_excel(lead_data):
    """
    Appends a dictionary of lead data to an Excel file.
    """
    # Add a timestamp to the data
    lead_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a DataFrame for the new single row
    new_row_df = pd.DataFrame([lead_data])
    
    if not os.path.exists(LEADS_FILE):
        # File doesn't exist: Create it with headers
        new_row_df.to_excel(LEADS_FILE, index=False, engine='openpyxl')
    else:
        # File exists: Append to it
        # We read existing data first (safest way for Excel)
        existing_df = pd.read_excel(LEADS_FILE)
        updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
        updated_df.to_excel(LEADS_FILE, index=False, engine='openpyxl')
        
    print(f"💾 Saved lead to {LEADS_FILE}")
    
    
def log_conversation(phone_number, sender, message, user_details=None, lead_captured=False):
    """
    Logs chat to 'chat_logs/{phone_number}.csv'
    """
    # 1. Ensure Log Directory Exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 2. Define Filename (Sanitize phone number just in case)
    safe_phone = phone_number.replace(":", "").replace("+", "")
    file_path = os.path.join(LOG_DIR, f"{safe_phone}.csv")
    
    # 3. Prepare Data
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Convert dict to string for CSV storage if it exists
    user_details_str = json.dumps(user_details) if user_details else ""
    
    # 4. Write to CSV
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write Header if new file
        if not file_exists:
            writer.writerow(["Date", "Time", "Sender", "Message", "User Details", "Lead Captured"])
            
        # Write Row
        writer.writerow([
            date_str, 
            time_str, 
            sender, 
            message, 
            user_details_str, 
            lead_captured
        ])