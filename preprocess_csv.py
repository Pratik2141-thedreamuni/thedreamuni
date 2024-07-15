import csv
import os

def preprocess_csv(file_path, cleaned_file_path):
    cleaned_rows = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        num_fields = len(headers)
        cleaned_rows.append(headers)
        
        for row in reader:
            if len(row) == num_fields:
                cleaned_rows.append(row)
            else:
                # Fix row by truncating or padding with empty values
                if len(row) > num_fields:
                    row = row[:num_fields]
                else:
                    row.extend([''] * (num_fields - len(row)))
                cleaned_rows.append(row)
    
    with open(cleaned_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(cleaned_rows)

# Usage
current_dir = os.path.dirname(os.path.abspath(__file__))
university_data_file = os.path.join(current_dir, 'university_rankings.csv')
cleaned_university_data_file = os.path.join(current_dir, 'cleaned_university_rankings.csv')

preprocess_csv(university_data_file, cleaned_university_data_file)
