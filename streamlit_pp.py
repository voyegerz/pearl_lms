import os
import json
import streamlit as st
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Please set it in the environment variables.")
    st.stop()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3
)

with open("courses.json", "r") as file:
    courses = json.load(file)

def find_relevant_courses(user_interest, user_goal):
    recommendations = []
    for course in courses:
        for tag in course["tags"]:
            if fuzz.partial_ratio(user_interest.lower(), tag.lower()) > 85 or \
               fuzz.partial_ratio(user_goal.lower(), tag.lower()) > 85:
                recommendations.append(course)
                break  
    return recommendations

def generate_learning_roadmap(user_data):
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
    Give the output in plain text.
    """

    try:
        response = llm.invoke([system_prompt, user_prompt])
        return response.content  
    except Exception as e:
        return "Failed to generate roadmap due to an AI error."


st.set_page_config(page_title="Career Chatbot", layout="wide")
st.title("🕵️‍♀️ Personal companion")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your learning journey today?"}]
if "user_data" not in st.session_state:
    st.session_state.user_data = {"age": None, "qualification": None, "interest": None, "goal": None}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ask me about learning paths, courses, or career guidance!")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    general_responses = {
        "hello": "Hello! How can I assist you today?",
        "hi": "Hi there! What can I help you with?",
        "how are you": "I'm just a chatbot, but I'm here to help you!",
        "what can you do": "I can guide you on learning paths, recommend courses, and generate a career roadmap."
    }

    response = None
    for key, val in general_responses.items():
        if key in user_input.lower():
            response = val
            break

    if not response:
        missing_details = [key for key, val in st.session_state.user_data.items() if val is None]

        if missing_details:
            next_detail = missing_details[0]  
            response = f"Could you provide your {next_detail}? 😊"
            st.session_state.user_data[next_detail] = user_input  
        else:
            roadmap = generate_learning_roadmap(st.session_state.user_data)
            recommended_courses = find_relevant_courses(st.session_state.user_data["interest"], st.session_state.user_data["goal"])

            response = f"📍 **Here’s your personalized learning roadmap:**\n\n{roadmap}\n\n"
            response += "📚 **Recommended Courses:**\n"
            if recommended_courses:
                for course in recommended_courses:
                    response += f"- **{course['name']}**: {course['description']}\n"
            else:
                response += "No relevant courses found."

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)

