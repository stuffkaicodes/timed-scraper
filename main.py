import requests
import time
import pandas as pd
from datetime import datetime
import gspread
import schedule
from dotenv import load_dotenv
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load environment variables from the .env file
load_dotenv()

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and create a service object
service_account_file = os.getenv('SERVICE_ACCOUNT_FILE')
credentials = service_account.Credentials.from_service_account_file(
    service_account_file, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# Open the Google Sheet by its ID
spreadsheet_id = os.getenv('SPREADSHEET_ID')
sheet = service.spreadsheets()

# Function to get Shopee data
def get_shopee_data(keyword, limit=15):
    url = "https://shopee.com.sg/api/v2/search_items/"
    params = {
        "by": "price",
        "keyword": keyword,
        "limit": 20,
        "newest": 0,
        "order": "asc",  # Order by ascending price
        "page_type": "search"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            items = data["items"]
            # Extract necessary fields
            results = []
            for item in items[:limit]:
                product = {
                    "Name": item["name"],
                    "Price": item["price"] / 100000,  # Convert from cents to SGD
                    "Seller": item["shopid"],
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                results.append(product)
            return results
    else:
        print("Failed to fetch data:", response.status_code)
    return []

# Write data to Google Sheets
def update_google_sheet(sheet, data):
    if data:
        df = pd.DataFrame(data)
        # Clear existing data
        sheet.values().clear(spreadsheetId=spreadsheet_id, range='Sheet1').execute()
        # Update with new data
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='RAW',
            body={'values': [df.columns.values.tolist()] + df.values.tolist()}
        ).execute()
        print(f"Data updated at {datetime.now()}")
    else:
        print("No data to update.")
# Define your scraping and updating workflow
def run_scraper():
    keyword = "longevity cat food carton"
    data = get_shopee_data(keyword)
    if data:
        update_google_sheet(sheet, data)
        print(f"Updated data at {datetime.now()}")

# Schedule the scraper to run at specific intervals
schedule.every().day.at("00:00").do(run_scraper)  # Example: run every day at 9 AM
schedule.every().day.at("15:00").do(run_scraper)  # Example: run at 3 PM

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)
