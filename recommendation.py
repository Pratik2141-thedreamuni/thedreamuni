import pandas as pd
import openai
from data_processing import user_profiles
import re

def match_universities(profile, university_data):
    if university_data.empty:
        print("No university data available.")
        return pd.DataFrame()

    def criteria_match(row):
        try:
            tuition_fees = float(row.get('TuitionFees', 0))
        except ValueError:
            tuition_fees = 0

        budget_in_target_currency = float(profile['budget_in_target_currency'])

        criteria = {
            'education_match': profile['highest_education'].lower() in row.get('ProgramDetails', '').lower(),
            'ielts_match': profile['ielts_score'] >= row.get('IELTS', 0),
            'budget_match': tuition_fees <= budget_in_target_currency
        }
        weights = {
            'education_match': 0.4,
            'ielts_match': 0.3,
            'budget_match': 0.3
        }
        score = sum([weights[k] * v for k, v in criteria.items()])
        return score

    university_data['MatchScore'] = university_data.apply(criteria_match, axis=1)
    filtered_unis = university_data[university_data['MatchScore'] > 0.5]

    return filtered_unis.sort_values(by='MatchScore', ascending=False).head(5)

def get_personalized_recommendation(user_id, university_data):
    profile = user_profiles.get(user_id, {})
    profile_text = "\n".join([f"{key}: {value}" for key, value in profile.items()])

    matched_unis = match_universities(profile, university_data)
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

        -  Alternative Recommendations:
          1. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
          2. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
          3. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]
          4. University Name: [Name]
             Location: [Location]
             Program: [ProgramDetails]
             Tuition Fees: [TuitionFees]
             IELTS Requirement: [IELTS]   
        """
    else:
        initial_prompt = f"""
        User's Profile:
        {profile_text}

        Based on the user's profile, provide initial recommendations for universities that closely match the user's preferences.
        """
        
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Upgrading to a more advanced model
            messages=[
                {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed initial recommendations."},
                {"role": "user", "content": initial_prompt}
            ],
            max_tokens=1500
        )

        gpt_recommendations = gpt_response['choices'][0]['message']['content'].strip()

        uni_recommendations = "\n".join([
            f"- University Name: {row['Name']}\n  Location: {row['Location']}\n  Program: {row['ProgramDetails']}\n  Tuition Fees: {row['TuitionFees']}\n  IELTS Requirement: {row.get('IELTS', 'N/A')}"
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
        model="gpt-4o-mini",  # Upgrading to a more advanced model
        messages=[
            {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide personalized and detailed recommendations according to their Budget, IELTS Score, Country, and course."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    reply = response['choices'][0]['message']['content'].strip()
    return reply

def recognize_intent(message):
    intents = {
        "scholarships": ["scholarship", "financial aid", "funding", "bursary"],
        "admission_requirements": ["admission requirement", "entry requirement", "eligibility", "criteria"],
        "cultural_differences": ["culture", "cultural difference", "tradition", "custom"]
    }

    message_lower = message.lower()
    for intent, keywords in intents.items():
        if any(re.search(r'\b' + keyword + r'\b', message_lower) for keyword in keywords):
            return intent
    return "general"

# Example usage
message = "Can you tell me about the scholarships available?"
intent = recognize_intent(message)
print(f"Recognized intent: {intent}")

def handle_user_query(user_id, message, university_data):
    profile = user_profiles.get(user_id, {})
    profile_text = "\n".join([f"{key}: {value}" for key, value in profile.items()])

    intent = recognize_intent(message)
    
    if intent == "scholarships":
        system_message = "You are an expert in global university scholarships. Use the user's profile information to provide detailed information about available scholarships."
    elif intent == "admission_requirements":
        system_message = "You are an expert in university admission requirements. Use the user's profile information to provide detailed information about admission requirements."
    elif intent == "cultural_differences":
        system_message = "You are an expert in global cultural differences. Use the user's profile information to provide detailed information about cultural differences in the target country."
    elif intent == "part_time_jobs":
        system_message = "You are an expert in part-time job opportunities for students. Use the user's profile information to provide detailed information about part-time job availability."
    elif intent == "full_time_jobs":
        system_message = "You are an expert in full-time job opportunities for graduates. Use the user's profile information to provide detailed information about full-time job opportunities."
    elif intent == "rent":
        system_message = "You are an expert in housing and rental costs. Use the user's profile information to provide detailed information about rent and accommodation options."
    elif intent == "city_life":
        system_message = "You are an expert in urban and city life. Use the user's profile information to provide detailed information about living in the city."
    elif intent == "internships":
        system_message = "You are an expert in internship opportunities. Use the user's profile information to provide detailed information about available internships."
    else:
        system_message = "You are an educational advisor specialized in global universities. Use the user's profile information to provide detailed and specific responses to their queries."

    prompt = f"""
    User's Profile:
    {profile_text}

    Conversation History:
    {conversation_history}

    User's Query: {message}

    {system_message}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o mini",  # Upgrading to a more advanced model
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    reply = response['choices'][0]['message']['content'].strip()

    # Check if a follow-up question should be asked
    if intent in follow_up_questions:
        follow_up_data = follow_up_questions[intent]
        follow_up_text = f"{follow_up_data['question']}\n" + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(follow_up_data['options'])])
        reply += f"\n\n{follow_up_text}"

    # Append the current message and response to the conversation history
    conversation_history.append({"user": message, "bot": reply})
    profile["conversation_history"] = conversation_history
    user_profiles[user_id] = profile

    return reply


def recognize_intent(message):
    intents = {
        "scholarships": ["scholarship", "financial aid", "funding", "bursary"],
        "admission_requirements": ["admission requirement", "entry requirement", "eligibility", "criteria"],
        "cultural_differences": ["culture", "cultural difference", "tradition", "custom"],
        "part_time_jobs": ["part-time job", "part time job", "part-time work", "part time work", "side job"],
        "full_time_jobs": ["full-time job", "full time job", "career", "employment"],
        "rent": ["rent", "housing cost", "accommodation cost", "living cost"],
        "city_life": ["city life", "urban life", "local life", "city experience"],
        "internships": ["internship", "internships", "intern"],
    }

    message_lower = message.lower()
    for intent, keywords in intents.items():
        if any(re.search(r'\b' + keyword + r'\b', message_lower) for keyword in keywords):
            return intent
    return "general"

def is_follow_up_option(message):
    message_lower = message.lower()
    for category, data in follow_up_questions.items():
        for option in data['options']:
            if re.search(r'\b' + re.escape(option.lower()) + r'\b', message_lower):
                return category, option
    return None, None

def handle_user_query(user_id, message, university_data):
    profile = user_profiles.get(user_id, {})
    profile_text = "\n".join([f"{key}: {value}" for key, value in profile.items()])

    prompt = f"""
    User's Profile:
    {profile_text}

    User's Query: {message}

    As an educational advisor, provide a specific and concise response to the user's query. Focus on directly answering the question asked, while leveraging your expertise as a study abroad consultant. Ensure the response is unbiased, ethical, and maintains user privacy.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an educational advisor specialized in global universities. Use the user's profile information to provide concise and specific responses to their queries. Directly address the question asked with relevant and precise information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    reply = response['choices'][0]['message']['content'].strip()
    return reply
