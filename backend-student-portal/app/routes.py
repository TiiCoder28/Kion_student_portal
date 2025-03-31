from flask import Blueprint, request, jsonify
from openai import OpenAI  # Import the new OpenAI client
import os
from datetime import datetime
from app.database import db
from auth.models import Message, Conversation, User
from flask_jwt_extended import jwt_required, get_jwt_identity
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
        "- Suggest tools and resources to enhance productivity.\n"
        "- Encourage self-assessment and reflection on progress.\n"
        "- Provide motivational support and tips for maintaining focus.\n"
        "-Provide the study tips in a structured format:\n"
        "1. **Understanding the student**: Ask about their study habits and goals.\n"
        "2. **Study plan**: Provide a personalized study plan using methods like active recall and spaced repetition.\n"
        "3. **Time management**: Offer time management strategies.\n"
        "4. **Tools and resources**: Suggest tools and resources to enhance productivity.\n"
        "5. **Self-assessment**: Encourage self-assessment and reflection on progress.\n"
        "6. **Motivational support**: Provide motivational support and tips for maintaining focus.\n"
        "7. **Next Steps**: Ask if the student needs more clarification or another example."
    )
}

def get_conversation_context(conversation_id):
    """Retrieve conversation messages from database and format for OpenAI"""
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    return formatted_messages



@chat_bp.route("/chat", methods=["POST"], endpoint='general_chat')
@jwt_required()  # Require authentication
def general_chat():
    """Handles chat messages and saves to database."""
    data = request.json
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')  # Now required
    user_id = get_jwt_identity()  # Get user ID from JWT token

    # Validate input
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    # Verify the conversation belongs to the user
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=user_id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Save user message to database
    user_msg = Message(
        conversation_id=conversation_id,
        content=user_message,
        role="user"
    )
    db.session.add(user_msg)

    # Get the full conversation history from database
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    
    # Format for OpenAI (include system prompt)
    openai_messages = [{
        "role": "system",
        "content": assistant_modes.get("assignment_help")  # Default mode
    }] + [{
        "role": msg.role,
        "content": msg.content
    } for msg in messages]

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages,
            temperature=0.3
        )

        ai_response = response.choices[0].message.content.strip()

        # Save AI response to database
        ai_msg = Message(
            conversation_id=conversation_id,
            content=ai_response,
            role="assistant"
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
        return jsonify({"error": "Chat failed"}), 500

@chat_bp.route("/conversations", methods=["GET"], endpoint='get_conversations')
@jwt_required()
def get_conversations():
    """Get all conversations for the current user"""
    user_id = get_jwt_identity()
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



@chat_bp.route("/conversations", methods=["POST"], endpoint='create_conversation')
@jwt_required()
def create_conversation():
    """Create a new conversation"""
    user_id = get_jwt_identity()
    mode = request.json.get('mode', 'assignment_help')
    
    new_conversation = Conversation(
        user_id=user_id,
        title=f"{mode.replace('_', ' ').title()} - {datetime.now().strftime('%b %d')}"
    )
    db.session.add(new_conversation)
    db.session.flush()
    
    # Add system prompt as first message
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

@chat_bp.route("/conversations/<int:conversation_id>", methods=["GET"], endpoint='get_conversation_in_chat')
@jwt_required()
def get_conversation(conversation_id):
    """Get a specific conversation with its messages"""
    user_id = get_jwt_identity()
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

@chat_bp.route("/conversations/<int:conversation_id>/chat", methods=["POST"], endpoint='chat_in_conversation')
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