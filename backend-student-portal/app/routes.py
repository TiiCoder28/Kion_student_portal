from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI  # Import the new OpenAI client
import os
from dotenv import load_dotenv
from datetime import datetime
from auth.models import User, Conversation, Message
from app.database import db

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
    )
}


def get_conversation_context(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    
    return [{"role": msg.role, "content": msg.content} for msg in messages]

@chat_bp.route("/chat", methods=["POST"], endpoint="general_chat")
@jwt_required()
def general_chat():
    data = request.json
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    user_id = get_jwt_identity()

    if not user_message or not conversation_id:
        return jsonify({"error": "Missing required fields"}), 400

    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    try:
        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            content=user_message,
            role="user"
        )
        db.session.add(user_msg)

        # Get conversation context
        messages = get_conversation_context(conversation_id)
        openai_messages = [{
            "role": "system",
            "content": assistant_modes.get("assignment_help")
        }] + messages

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages,
            temperature=0.3
        )

        ai_response = response.choices[0].message.content.strip()

        # Save AI response
        ai_msg = Message(
            conversation_id=conversation_id,
            content=ai_response,
            role="assistant",
            tokens=response.usage.total_tokens if hasattr(response, 'usage') else None
        )
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({
            "response": ai_response,
            "conversation_id": conversation_id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/conversations", methods=["GET"], endpoint="get_conversations")
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    try:
        conversations = db.session.query(
            Conversation,
            db.func.max(Message.created_at).label('last_activity')
        ).join(Message)\
         .filter(Conversation.user_id == user_id)\
         .group_by(Conversation.id)\
         .order_by(db.desc('last_activity'))\
         .all()
        
        return jsonify([{
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "last_activity": last_activity.isoformat() if last_activity else conv.created_at.isoformat(),
            "message_count": len(conv.messages)
        } for conv, last_activity in conversations])
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return jsonify({"error": "Failed to fetch conversations"}), 500

@chat_bp.route("/conversations", methods=["POST"], endpoint="create_conversation")
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    mode = request.json.get('mode', 'assignment_help')
    
    try:
        new_conversation = Conversation(
            user_id=user_id,
            title=f"{mode.replace('_', ' ').title()} - {datetime.now().strftime('%b %d')}"
        )
        db.session.add(new_conversation)
        db.session.flush()  # Get the ID before commit
        
        system_message = Message(
            conversation_id=new_conversation.id,
            content=assistant_modes.get(mode, assistant_modes["assignment_help"]),
            role="system"
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            "id": new_conversation.id,
            "title": new_conversation.title
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating conversation: {e}")
        return jsonify({"error": "Failed to create conversation"}), 500

@chat_bp.route("/conversations/<int:conversation_id>", methods=["GET"], endpoint="get_conversation")
@jwt_required()
def get_conversation(conversation_id):
    user_id = get_jwt_identity()
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=user_id
        ).first_or_404()
        
        messages = Message.query.filter_by(conversation_id=conversation_id)\
                      .order_by(Message.created_at.asc()).all()
        
        return jsonify({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": [{
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            } for msg in messages]
        })
    except Exception as e:
        print(f"Error fetching conversation: {e}")
        return jsonify({"error": "Conversation not found"}), 404
    
@chat_bp.route("/conversations/<int:conversation_id>/chat", methods=["POST"])
@jwt_required()
def chat(conversation_id):
    """Handle chat messages within a specific conversation"""
    user_id = get_jwt_identity()
    data = request.json
    user_message = data.get('message', '').strip()
    
    # Verify conversation belongs to user
    conversation = Conversation.query.filter_by(
        id=conversation_id, 
        user_id=user_id
    ).first_or_404()
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Save user message to database
    user_msg = Message(
        conversation_id=conversation_id,
        content=user_message,
        role="user"
    )
    db.session.add(user_msg)
    
    # Get conversation context for OpenAI
    messages = get_conversation_context(conversation_id)
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # Updated to current model
            messages=messages,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Save AI response to database
        ai_msg = Message(
            conversation_id=conversation_id,
            content=ai_response,
            role="assistant",
            tokens=response.usage.total_tokens if hasattr(response, 'usage') else None
        )
        db.session.add(ai_msg)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "response": ai_response,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500