import pandas as pd
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the university data file path
university_data_file = 'university_rankings_shuffled.csv'

# Store user profiles
user_profiles = {}

def load_and_preprocess_data():
    try:
        university_data = pd.read_csv(university_data_file, on_bad_lines='skip')
        if university_data.empty:
            print("CSV file is empty.")
            university_data = pd.DataFrame()
    except pd.errors.ParserError as e:
        print(f"Error reading {university_data_file}: {e}")
        university_data = pd.DataFrame()
    
    return preprocess_data(university_data)

def preprocess_data(df):
    df = df.dropna(subset=['Name', 'Location', 'ProgramDetails', 'TuitionFees'])
    df['TuitionFees'] = pd.to_numeric(df['TuitionFees'].str.replace(',', ''), errors='coerce')

    if 'IELTS' in df.columns:
        df['IELTS'] = df['IELTS'].apply(lambda x: pd.to_numeric(re.search(r'(\d+\.\d+|\d+)', str(x)).group(0), errors='coerce') if pd.notna(x) and re.search(r'(\d+\.\d+|\d+)', str(x)) else pd.NA)
    else:
        df['IELTS'] = pd.NA

    if 'Grades' in df.columns:
        df['Grades'] = df['Grades'].apply(lambda x: pd.to_numeric(re.search(r'(\d+\.\d+|\d+)', str(x)).group(0), errors='coerce') if pd.notna(x) and re.search(r'(\d+\.\d+|\d+)', str(x)) else pd.NA)
    else:
        df['Grades'] = pd.NA

    return df

def scrape_universities():
    # Placeholder for scraping logic
    # Return a DataFrame after scraping
    df = pd.DataFrame()
    return df
