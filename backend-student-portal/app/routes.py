from flask import Blueprint, request, jsonify
from openai import OpenAI  # Import the new OpenAI client
import os
from dotenv import load_dotenv

load_dotenv()

# Create a Blueprint for the chat route
chat_bp = Blueprint("chat", __name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dictionary to store conversation history for each session
conversation_history = {}

@chat_bp.route("/chat", methods=["POST"])
def chat():
    # Get the JSON data from the request
    data = request.json
    user_message = data.get('message', '')
    chat_type = data.get('chat_type', 'assignment_help')  # Default to assignment help
    session_id = data.get('session_id', 'default_session')  # Unique session ID for each chat

    # Validate the input
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Define system prompts for each chat type
    system_prompts = {
        "assignment_help": "You are a helpful assistant designed to assist high school students with their assignments. Ask probing questions to find out where they need assistance.",
        "study_tips": "You are a helpful assistant designed to assist high school students and offer study tips based on their study style, the course they chose, when the test or exam is, and how often they'd like to study. Ask further probing questions, then offer them study tips for effective and successful studying."
    }

    # Get the system prompt based on the chat type
    system_prompt = system_prompts.get(chat_type, system_prompts["assignment_help"])

    # Initialize conversation history for the session if it doesn't exist
    if session_id not in conversation_history:
        conversation_history[session_id] = [
            {"role": "system", "content": system_prompt}
        ]

    # Add the user's message to the conversation history
    conversation_history[session_id].append({"role": "user", "content": user_message})

    try:
        # Call the OpenAI API using the chat completions endpoint
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a valid model like gpt-3.5-turbo or gpt-4
            messages=conversation_history[session_id],  # Pass the entire conversation history
            max_tokens=150,  # Adjust as needed
            temperature=0.7  # Adjust as needed
        )

        # Extract the AI's response
        ai_response = response.choices[0].message.content.strip()

        # Add the AI's response to the conversation history
        conversation_history[session_id].append({"role": "assistant", "content": ai_response})

        # Return the AI's response as JSON
        return jsonify({"response": ai_response})

    except Exception as e:
        # Log the full error for debugging
        print(f"Error calling OpenAI API: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {e.args}")
        return jsonify({"error": "An error occurred while processing your request"}), 500