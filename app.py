from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import openai  # Import the OpenAI module
from data_processing import load_and_preprocess_data, scrape_universities, user_profiles
from recommendation import get_personalized_recommendation, handle_user_query

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load and preprocess university data
university_data = load_and_preprocess_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_countries', methods=['GET'])
def get_countries():
    countries = [
        "Argentina", "Australia", "Austria", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Benin",
        "Bhutan", "Bolivia", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chile", "China", "Colombia",
        "Congo, Democratic Republic of the", "Costa Rica", "Croatia", "Czech Republic", "Denmark", "Dominican Republic",
        "Ecuador", "Egypt", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Georgia", "Germany",
        "Greece", "Grenada", "Hungary", "India", "Indonesia", "Iran", "Ireland", "Israel", "Italy", "Japan", "Jordan",
        "Korea, South", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Lithuania", "Luxembourg", "Malawi", "Malaysia",
        "Mexico", "Moldova", "Monaco", "Mongolia", "Netherlands", "New Zealand", "Niger", "Nigeria", "North Macedonia", "Norway",
        "Oman", "Pakistan", "Panama", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Saint Kitts and Nevis",
        "Saint Vincent and the Grenadines", "Serbia", "Seychelles", "Singapore", "Slovakia", "Slovenia", "South Africa",
        "Spain", "Sri Lanka", "Sweden", "Switzerland", "Taiwan", "Tajikistan", "Thailand", "Trinidad and Tobago", "Turkey",
        "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan",
        "Vietnam", "Zambia", "Zimbabwe"
    ]
    return jsonify(countries)

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
            "other_education": data.get("otherEducation"),
            "subject": data.get("subject"),
            "ielts_score": data.get("ieltsScore"),
            "target_country": target_country,
            "study_pursue": data.get("studyPursue"),
            "other_study": data.get("otherStudy"),
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
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed study recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )

            reply = response['choices'][0]['message']['content'].strip()
            return jsonify({"reply": reply})

        reply = get_personalized_recommendation(user_id, university_data)
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
        
        reply = handle_user_query(user_id, message, university_data)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    df = scrape_universities()
    return jsonify({"status": "success", "message": "Data scraped and saved.", "data": df.to_dict()})

if __name__ == '__main__':
    app.run(debug=True)
