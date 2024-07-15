import os
import pandas as pd

file_path = 'university_rankings.csv'

def check_csv_columns(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, on_bad_lines='skip')
        print("Columns in the CSV file:", df.columns)
    else:
        print(f"CSV file {file_path} does not exist.")

check_csv_columns(file_path)
