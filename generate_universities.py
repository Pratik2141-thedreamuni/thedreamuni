import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
import os
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Track unique universities
unique_universities = set()

# URLs to scrape data from
urls = {
    'Germany': 'URL_TO_SCRAPE',  # Replace with the actual URL
}

def scrape_universities():
    universities = []

    for country, url in urls.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes
            soup = BeautifulSoup(response.text, 'html.parser')

            # Scrape university names and details
            for row in soup.select('table tbody tr'):
                columns = row.find_all('td')
                if len(columns) > 1:  # Ensure there are enough columns
                    name = columns[1].text.strip()
                    location = f"{country}"
                    if name not in unique_universities:
                        unique_universities.add(name)
                        universities.append({
                            "Name": name,
                            "Location": location,
                            "Ranking": "Not Ranked",
                            "Programs": [{"ProgramName": "General Program", "Requirements": "Varies", "TuitionFees": "Varies", "Grades": "Varies", "IELTS": "Varies"}]
                        })
        except requests.RequestException as e:
            print(f"Failed to fetch data from {url}: {e}")
        except IndexError:
            print(f"Failed to parse data from {url}")

    return universities

def generate_university_data(existing_universities):
    prompt = f"""
    List non-popular universities from Germany with the following details:
    1. Name
    2. Location
    3. Ranking
    4. Program Details (at least 10 different programs with specific requirements for each, including grades and IELTS score)
    5. Tuition Fees
    
    Include a diverse set of universities, not just top-ranked ones, and provide their program-specific requirements.
    Exclude the following universities:
    """
    prompt += "\n".join(existing_universities) + "\n"

    prompt += """
    Ensure that universities from Germany are not in the top rankings.
    Format the response as a JSON array of objects with keys: "Name", "Location", "Ranking", "Programs" where "Programs" is an array of objects with keys: "ProgramName", "Requirements", "TuitionFees", "Grades", "IELTS".
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant that provides information about universities."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.7
    )

    return response['choices'][0]['message']['content'].strip()

def save_to_csv(data, file_path):
    try:
        # Remove triple backticks from the JSON string if they exist
        data = data.strip("```json").strip("```")

        university_list = json.loads(data)  # Convert the JSON string to a Python object

        rows = []
        for uni in university_list:
            # Check if university is not top-ranked and from Germany
            if uni['Location'] == 'Germany' and 'top-ranked' in uni['Ranking'].lower():
                continue

            if uni['Name'] not in unique_universities:
                unique_universities.add(uni['Name'])
                for program in uni['Programs']:
                    rows.append({
                        "Name": uni['Name'],
                        "Location": uni['Location'],
                        "Ranking": uni['Ranking'],
                        "ProgramName": program['ProgramName'],
                        "Requirements": program['Requirements'], 
                        "TuitionFees": program['TuitionFees'],
                        "Grades": program['Grades'],
                        "IELTS": program['IELTS']
                    })

        df = pd.DataFrame(rows)
        if os.path.exists(file_path):
            df.to_csv(file_path, mode='a', index=False, header=False)
        else:
            df.to_csv(file_path, index=False)
        print(f"Data saved to {file_path}")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    file_path = 'university_rankings.csv'
    num_batches = 1000  # Number of batches to generate
    batch_size = 30    # Number of universities per batch

    # Scrape initial set of universities
    scraped_universities = scrape_universities()
    save_to_csv(json.dumps(scraped_universities), file_path)

    # Generate additional data using OpenAI API
    for _ in range(num_batches):
        data = generate_university_data(unique_universities)
        if data:
            save_to_csv(data, file_path)
        else:
            print("No data received from OpenAI.")
        time.sleep(1)  # Sleep to avoid hitting rate limits

    print("Data generation complete.")
