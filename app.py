from flask import Flask, request, jsonify, render_template
import openai
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the university data file path
university_data_file = 'university_rankings.csv'

# Load university data
try:
    university_data = pd.read_csv(university_data_file, on_bad_lines='skip')
    if university_data.empty:
        print("CSV file is empty.")
        university_data = pd.DataFrame()
except pd.errors.ParserError as e:
    print(f"Error reading {university_data_file}: {e}")
    university_data = pd.DataFrame()

# Store user profiles
user_profiles = {}

@app.route('/')
def index():
    return render_template('index.html')

def match_universities(profile):
    if university_data.empty:
        print("No university data available.")
        return pd.DataFrame()

    # Define threshold for partial match
    threshold = 0.6

    def criteria_match(row):
        match_count = 0
        criteria = [
            profile['subject'].lower() in row.get('ProgramDetails', '').lower(),
            profile['highest_education'].lower() in row.get('ProgramDetails', '').lower(),
            str(profile['ielts_score']) in str(row.get('IELTS', '')),
            str(profile['grades']) in str(row.get('Grades', '')),
            row.get('TuitionFees', '0').replace(',', '').isdigit() and float(row.get('TuitionFees', '0').replace(',', '')) <= profile['budget_in_target_currency']
        ]
        match_count = sum(criteria)
        return match_count / len(criteria)

    # Filter universities based on the user's profile with a threshold for partial match
    university_data['MatchScore'] = university_data.apply(criteria_match, axis=1)
    filtered_unis = university_data[university_data['MatchScore'] >= threshold]

    return filtered_unis.sort_values(by='MatchScore', ascending=False).head(5)

def get_personalized_recommendation(user_id):
    profile = user_profiles.get(user_id, {})
    profile_text = "\n".join([f"{key}: {value}" for key, value in profile.items()])

    matched_unis = match_universities(profile)
    if matched_unis.empty:
        prompt = f"""
        User's Profile:
        {profile_text}

        Provide alternative universities that closely match the user's profile but might not meet all criteria exactly. Ensure the recommendations are unbiased, ethical, and maintain user privacy. Format the recommendations as follows:

        -  Top Recommendation:
          University Name: [Name]
          Location: [Location]
          Program: [ProgramDetails]
          Tuition Fees: [TuitionFees]
          IELTS Requirement: [IELTS]
          Grades Requirement: [Grades]

        -  Alternative Recommendations:
          1. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
             Grades Requirement: [Grades]
          2. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
             Grades Requirement: [Grades]
          3. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
             Grades Requirement: [Grades]
        """
    else:
        uni_recommendations = "\n".join([
            f"- University Name: {row['Name']}\n  Location: {row['Location']}\n  Program: {row['ProgramDetails']}\n  Tuition Fees: {row['TuitionFees']}\n  IELTS Requirement: {row.get('IELTS', 'N/A')}\n  Grades Requirement: {row.get('Grades', 'N/A')}"
            for i, row in matched_unis.iterrows()
        ])
        reply = (
            f"User's Profile:\n{profile_text}\n"
            f"Based on the user's profile, here are some personalized university recommendations:\n{uni_recommendations}"
        )
        return reply

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed recommendations according to their Grades, Budget, IELTS Score, Country, and course."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    reply = response['choices'][0]['message']['content'].strip()
    return reply

def handle_user_query(user_id, message):
    profile = user_profiles.get(user_id, {})
    profile_text = "\n".join([f"{key}: {value}" for key, value in profile.items()])

    prompt = f"""
    User's Profile:
    {profile_text}

    User's Query: {message}

    As an educational advisor, provide a detailed and personalized response to the user's query. Include information about scholarships, accommodation, part-time jobs, work-life balance, healthcare, rent, future job opportunities, and any other relevant aspects.

    Ensure the response is unbiased, ethical, and maintains user privacy.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed responses to their queries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    reply = response['choices'][0]['message']['content'].strip()
    return reply

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        user_id = data.get("userId")
        target_country = data.get("targetCountry")
        budget = data.get("budget")

        # Convert budget to target country's currency
        currency_mapping = {
            "United States of America": "USD",
            "Germany": "EUR",
            "Canada": "CAD",
            "Australia": "AUD",
            "India": "INR"
        }
        user_profiles[user_id] = {
            "student_name": data.get("studentName"),
            "highest_education": data.get("highestEducation"),
            "grades": data.get("grades"),
            "ielts_score": data.get("ieltsScore"),
            "target_country": target_country,
            "study_pursue": data.get("studyPursue"),
            "subject": data.get("subject"),
            "budget_in_target_currency": budget,
            "currency": currency_mapping.get(target_country, "INR")
        }

        reply = get_personalized_recommendation(user_id)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error in /recommend: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("userId")
        message = data.get("message")
        if user_id not in user_profiles:
            return jsonify({"reply": "Please provide your profile information first."})
        
        reply = handle_user_query(user_id, message)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        user_id = data.get("userId")
        feedback = data.get("feedback")
        
        # Store or process the feedback
        if user_id in user_profiles:
            if "feedback" not in user_profiles[user_id]:
                user_profiles[user_id]["feedback"] = []
            user_profiles[user_id]["feedback"].append(feedback)
        
        return jsonify({"status": "success", "message": "Feedback received."})
    except Exception as e:
        print(f"Error in /feedback: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    df = scrape_universities()
    return jsonify({"status": "success", "message": "Data scraped and saved.", "data": df.to_dict()})
