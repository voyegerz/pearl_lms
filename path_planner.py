import os
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import json
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Initialize Gemini AI
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3
)

# Initialize Flask
app = Flask(__name__)
CORS(app)  

# Load courses from JSON
with open("courses.json", "r") as file:
    courses = json.load(file)

def find_relevant_courses(user_interest, user_goal):
    recommendations = []
    
    for course in courses:
        for tag in course["tags"]:
            # Fuzzy match threshold (above 70 is a good match)
            if fuzz.partial_ratio(user_interest.lower(), tag.lower()) > 85 or \
               fuzz.partial_ratio(user_goal.lower(), tag.lower()) > 85:
                recommendations.append(course)
                break  # No need to check other tags for this course

    return recommendations

def generate_learning_roadmap(user_data):
    """
    Use Gemini AI to generate a personalized learning roadmap.
    """
    system_prompt = """
    You are an AI mentor. Based on the user's age, qualification, and career goal,
    generate a structured step-by-step learning roadmap including essential skills, 
    technologies, projects, and industry best practices.
    """

    user_prompt = f"""
    User Details:
    - Age: {user_data['age']}
    - Qualification: {user_data['qualification']}
    - Interest: {user_data['interest']}
    - Career Goal: {user_data['goal']}

    Generate a structured learning roadmap for this user. 
    Provide steps including key subjects, tools, projects, and online resources.
    Give the output in plain text without any formatting.
    """

    try:
        response = llm.invoke([system_prompt, user_prompt])
        return response.content  # Extract AI-generated response
    except Exception as e:
        # print(f"Error in Gemini AI response: {e}")  # Debugging
        return "Failed to generate roadmap due to an AI error."

@app.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    try:
        user_data = request.get_json()
        
        # Validate user input
        required_keys = ["age", "qualification", "interest", "goal"]
        if not all(key in user_data for key in required_keys):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Find course recommendations
        recommended_courses = find_relevant_courses(user_data["interest"], user_data["goal"])
        # print(recommended_courses)
        
        # Generate AI-based roadmap
        roadmap = generate_learning_roadmap(user_data)
        
        # Prepare response
        response_data = {
            "roadmap": roadmap,
            "recommended_courses": recommended_courses if recommended_courses else "No relevant courses found."
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"Server Error: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
