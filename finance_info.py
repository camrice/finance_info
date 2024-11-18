import yfinance as yf
import requests
import datetime
import time
import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json
from dotenv import load_dotenv
from fredapi import Fred

# Load environment variables from .env file
load_dotenv()

from_email = os.getenv('EMAIL_USER')
from_email_password = os.getenv('EMAIL_PASS')
fred_api_key = os.getenv('FRED_API_KEY')

email_list = json.loads(os.getenv('EMAIL_LIST'))

# Initialize the Fred object
fred = Fred(api_key=fred_api_key)

# File where data will be saved
fred_data_file = 'us_20_year_treasury_yield.json'

def get_last_saved_gs20_value():
    if os.path.exists(fred_data_file):
        with open(fred_data_file, 'r') as file:
            data = json.load(file)
            last_updated_date = data.get('value', '')
            return last_updated_date
    return None

# Function to read the last updated date from the file
def get_last_updated_month():
    if os.path.exists(fred_data_file):
        with open(fred_data_file, 'r') as file:
            data = json.load(file)
            last_updated_date = data.get('last_updated', '')
            return last_updated_date
    return None

# Function to save the latest data to the file
def save_data(value, date):
    data = {
        'value': value,
        'last_updated': date,
    }

    with open(fred_data_file, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Data saved: {value} on {date}")

def get_current_month():
    # Get the current date
    current_date = datetime.datetime.today()

    return datetime.datetime(current_date.year, current_date.month, 1).strftime('%Y-%m')

def get_last_completed_month():
    # Get the current date
    current_date = datetime.datetime.today()

    # Determine the first day of the current month
    first_day_of_current_month = datetime.datetime(current_date.year, current_date.month, 1)

    # Subtract one day to get the last day of the previous month
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)

    # Get the last month and year as a string in the format "YYYY-MM"
    last_completed_month = last_day_of_previous_month.strftime('%Y-%m')

    return last_completed_month

def fetch_gs20():
    # Get the latest monthly value for the US 20-Year Treasury Yield (GS20)
    series_id = 'GS20'
    data = fred.get_series(series_id)

    # The latest value is the last element of the series
    latest_value = data.iloc[-1]
    return latest_value

def fetch_gs20_if_needed():
    # Get the last completed month
    previous_month = get_last_completed_month()

    # Get the last updated month from the file (if it exists)
    last_updated_month = get_last_updated_month()

    value = get_last_saved_gs20_value()

    if last_updated_month != previous_month:
        print(f"Updating data for {previous_month}...")
        value = fetch_gs20()
        date = get_last_completed_month()

        if value and date:
            save_data(value, date)
    else:
        print("Data is up to date. No update needed.")

    return value

# Function to fetch S&P 500, Nasdaq Composite, Treasury yields, and US 30 Year Treasury Yield
def fetch_financial_data():
    tickers = {
        "S&P 500": "^GSPC",         # S&P 500 Index
        "Nasdaq Composite": "^IXIC", # Nasdaq Composite Index
        "US 10 Year Treasury Yield": "^TNX",  # 10-Year Treasury Yield
        # "US 30 Year Treasury Yield": "^TYX",  # 30-Year Treasury Yield
    }

    data = {}

    # Fetch historical data for each ticker and use iloc to get the most recent opening price
    for label, ticker in tickers.items():
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")  # Fetch one day data

        # Convert the historical data to a pandas DataFrame
        # We use the 'Open' column to get the opening price for today
        ser = hist['Open']  # Get the 'Open' column for the current day
        data[label] = ser.iloc[-1]  # Use iloc to get the most recent open price (the current day's open)

    return data

# Function to fetch GBP to USD exchange rate using an API
def fetch_exchange_rate():
    url = "https://api.exchangerate-api.com/v4/latest/GBP"  # API endpoint for GBP to USD exchange rate
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['rates']['USD']  # Get the exchange rate for GBP to USD
    else:
        raise Exception("Error fetching exchange rate")

# Function to get the current time in UTC and convert it to a specified timezone (PST)
def get_current_time_in_timezone(timezone='US/Pacific'):
    # Get current UTC time
    utc_now = datetime.datetime.now(pytz.utc)

    # Convert UTC time to the desired timezone
    tz = pytz.timezone(timezone)
    local_time = utc_now.astimezone(tz)

    return local_time

# Function to send email with the data
def send_email(subject, body, to_email, from_email, from_email_password):
    # Set up the MIME (Multipurpose Internet Mail Extensions) object
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the body with the email
    msg.attach(MIMEText(body, 'plain'))

    # Set up the SMTP server (using Gmail's SMTP server as an example)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(from_email, from_email_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Main function
def main():
    # Get the current time in PST
    local_time = get_current_time_in_timezone('US/Pacific')
    today = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Fetch the latest financial data (Open values for today)
    financial_data = fetch_financial_data()

    # Fetch exchange rate
    exchange_rate = fetch_exchange_rate()

    # Fetch US 20 year treasury yield
    gs20 = fetch_gs20_if_needed()

    # Format the email body
    email_body = f"Data for {today}:\n\n"
    for label, value in financial_data.items():
        email_body += f"{label} Open: {value:.2f}\n"

    email_body += f"Exchange rate for GBP to USD: {exchange_rate:.4f}\n"
    email_body += f"FRED GS20 for {get_last_completed_month()}: {gs20:.2f}\n"

    # Email details
    subject = "Financial Data Update"

    # Send the emails
    for to_email in email_list:
        send_email(subject, email_body, to_email, from_email, from_email_password)
        time.sleep(5)

if __name__ == "__main__":
    main()
