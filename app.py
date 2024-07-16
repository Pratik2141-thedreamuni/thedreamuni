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

@app.route('/get_countries', methods=['GET'])
def get_countries():
    countries = [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
        "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas",
        "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin",
        "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
        "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
        "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia",
        "Comoros", "Congo, Democratic Republic of the", "Congo, Republic of the",
        "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark",
        "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
        "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji",
        "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
        "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
        "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq",
        "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
        "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kosovo", "Kuwait",
        "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
        "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia",
        "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
        "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
        "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands",
        "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway",
        "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
        "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
        "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
        "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal",
        "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
        "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka",
        "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
        "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
        "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine",
        "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay",
        "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
        "Zambia", "Zimbabwe"
    ]
    return jsonify(countries)

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
        # Combining GPT-3.5 recommendations with the university data
        initial_prompt = f"""
        User's Profile:
        {profile_text}

        Based on the user's profile, provide initial recommendations for universities that closely match the user's preferences.
        """
        
        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed initial recommendations."},
                {"role": "user", "content": initial_prompt}
            ],
            max_tokens=1500
        )

        gpt_recommendations = gpt_response['choices'][0]['message']['content'].strip()

        uni_recommendations = "\n".join([
            f"- University Name: {row['Name']}\n  Location: {row['Location']}\n  Program: {row['ProgramDetails']}\n  Tuition Fees: {row['TuitionFees']}\n  IELTS Requirement: {row.get('IELTS', 'N/A')}\n  Grades Requirement: {row.get('Grades', 'N/A')}"
            for i, row in matched_unis.iterrows()
        ])
        
        reply = (
            f"User's Profile:\n{profile_text}\n"
            f"Based on the user's profile, here are some personalized university recommendations:\n\n"
            f"{gpt_recommendations}\n\n"
            f"Additional university recommendations from our database:\n{uni_recommendations}"
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

    As an educational advisor, provide a specific and concise response to the user's query. Focus on directly answering the question asked, while leveraging your expertise as a study abroad consultant. Ensure the response is unbiased, ethical, and maintains user privacy.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide concise and specific responses to their queries. Directly address the question asked with relevant and precise information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500  # Reduced max tokens to encourage concise responses
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

        if data.get("studyIdea") == "notDecided":
            profile_text = "\n".join([f"{key}: {value}" for key, value in user_profiles[user_id].items()])
            prompt = f"""
            User's Profile:
            {profile_text}

            Suggest suitable studies based on the user's preferences and qualifications. Ensure the recommendations are unbiased, ethical, and maintain user privacy. Format the recommendations as follows:

            -  Recommended Study:
              Study Name: [Name]
              Reason: [Reason]

            Provide a detailed and personalized response.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed study recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )

            reply = response['choices'][0]['message']['content'].strip()
            return jsonify({"reply": reply})

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
    
