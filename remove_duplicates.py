import pandas as pd

file_path = 'university_rankings.csv'

def remove_duplicates(file_path):
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
        df.drop_duplicates(subset=['Name', 'ProgramDetails'], keep='first', inplace=True)
        df.to_csv(file_path, index=False)
        print("Duplicates removed and data saved.")
    except pd.errors.ParserError as e:
        print(f"Error reading CSV file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    remove_duplicates(file_path)
