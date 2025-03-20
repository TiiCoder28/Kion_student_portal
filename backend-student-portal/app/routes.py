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

# System prompts for different assistant modes
assistant_modes = {
    "assignment_help": (
        "You are a structured AI tutor helping students step by step with assignments. "
        "Follow this format in responses: \n"
        "1. **Understanding the problem**: Ask clarifying questions.\n"
        "2. **Concept explanation**: Provide definitions and examples.\n"
        "3. **Suggested approach**: Outline a step-by-step solution strategy.\n"
        "4. **Example solution**: Offer a partial example without just giving the full answer.\n"
        "5. **Next Steps**: Ask if the student needs more clarification or another example."
    ),
    "study_tips": (
        "You are a structured study coach providing effective learning strategies.\n"
        "- Start by asking about the student's study habits and goals.\n"
        "- Provide a personalized study plan using methods like active recall and spaced repetition.\n"
        "- Offer time management strategies.\n"
        "- Suggest tools and resources to enhance productivity."
    ),
    "essay_helper": (
        "You are an AI assistant helping students plan and outline their essays.\n"
        "Follow this structured approach: \n"
        "1. **Understand the topic**: Ask the student for their thesis or main idea.\n"
        "2. **Outline the structure**: Suggest an introduction, body paragraphs, and conclusion.\n"
        "3. **Provide writing tips**: Explain how to strengthen arguments with evidence.\n"
        "4. **Suggest improvements**: Offer constructive feedback on clarity and flow."
    )
}

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Handles structured AI assistant requests."""
    data = request.json
    user_message = data.get('message', '').strip()
    mode = data.get('mode', 'assignment_help')  # Default to assignment help
    session_id = data.get('session_id', 'default_session')  # Unique session ID

    # Validate input
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Get the appropriate assistant mode
    system_prompt = assistant_modes.get(mode, assistant_modes["assignment_help"])

    # Initialize conversation history for the session if it doesn't exist
    if session_id not in conversation_history:
        conversation_history[session_id] = [{"role": "system", "content": system_prompt}]

    # Add user's message to the conversation history
    conversation_history[session_id].append({"role": "user", "content": user_message})

    try:
        # Call OpenAI API using structured responses
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=conversation_history[session_id],
            temperature=0.3
        )

        # Extract AI's structured response
        ai_response = response.choices[0].message.content.strip()

        # Add AI's response to conversation history
        conversation_history[session_id].append({"role": "assistant", "content": ai_response})

        # Return structured JSON response
        return jsonify({
            "mode": mode,
            "response": ai_response,
            "next_steps": "Would you like further clarification or an example?"
        })

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500
