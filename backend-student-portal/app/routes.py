from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI  # Import the new OpenAI client
import os
from dotenv import load_dotenv
from datetime import datetime
from auth.models import User
import uuid
from auth.models import ChatSession, ChatMessage, db

load_dotenv()

chat_bp = Blueprint("chat", __name__)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
@jwt_required()
def chat():
    """Handles structured AI assistant requests."""
    data = request.json
    user_message = data.get('message', '').strip()
    chat_type = data.get('chat_type', 'assignment_help')
    session_id = data.get('session_id', str(uuid.uuid4()))
    user_id = get_jwt_identity()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if chat_type not in assistant_modes:
        return jsonify({"error": "Invalid chat type"}), 400


    # Check if user has too many active chats
    active_chats = ChatSession.query.filter_by(user_id=user_id).count()
    if active_chats >= 5:
        return jsonify({"error": "You've reached the maximum number of active chats (5)"}), 400


    # Get or create chat session
    session = ChatSession.query.get(session_id)
    if not session:
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=f"{chat_type.replace('_', ' ').title()} - {datetime.now().strftime('%b %d')}",
            chat_type=chat_type
        )
        db.session.add(session)
        db.session.commit()

   # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        sender='user',
        content=user_message
    )
    db.session.add(user_msg)

  
    system_prompt = assistant_modes[chat_type]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=128000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Save AI response
        ai_msg = ChatMessage(
            session_id=session_id,
            sender='ai',
            content=ai_response
        )
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({
            "response": ai_response,
            "session_id": session_id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chats", methods=["GET"])
@jwt_required()
def get_user_chats():
    user_id = get_jwt_identity()
    
    # Verify user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()
    return jsonify([{
        "id": s.id,
        "title": s.title,
        "type": s.chat_type,
        "created_at": s.created_at.isoformat()  # Consistent date format
    } for s in sessions])



@chat_bp.route("/chats/<session_id>", methods=["GET"])
@jwt_required()
def get_chat_messages(session_id):
    user_id = get_jwt_identity()
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"error": "Chat not found"}), 404
        
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    return jsonify([{
        "sender": m.sender,
        "content": m.content,
        "timestamp": m.timestamp.isoformat()
    } for m in messages])