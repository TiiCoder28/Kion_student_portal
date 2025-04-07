from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from auth.models import Conversation, Message
from app.database import db
import re
from typing import List, Dict, Optional

load_dotenv()

chat_bp = Blueprint("chat", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


conversation_history = {}

class Agent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4",
        tools: Optional[List] = None,
        handoffs: Optional[List['Agent']] = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self.handoffs = handoffs or []

    def generate_response(self, messages: List[Dict]) -> str:
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.instructions},
                    *messages
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in {self.name} agent: {e}")
            raise

math_agent = Agent(
    name="Math Tutor (CAPS)",
    instructions=(
        "You are a mathematics tutor specializing in the South African CAPS curriculum for Grades 10-12.\n"
        "Help with: Algebra, Calculus, Geometry, Trigonometry\n"
        "Always explain concepts step-by-step with examples.\n"
        "Format math expressions using $$LaTeX$$.\n"
        "Encourage problem-solving rather than giving direct answers."
    )
)

english_agent = Agent(
    name="English Tutor (CAPS)",
    instructions=(
        "You are an English tutor for the South African CAPS curriculum.\n"
        "Help with: Essay writing, Poetry analysis, Grammar, Prescribed texts\n"
        "Focus on developing critical analysis and clear communication skills.\n"
        "Provide constructive feedback on writing samples."
    )
)

general_tutor_agent = Agent(
    name="General Tutor",
    instructions=(
        "You are a knowledgeable tutor helping with general academic subjects.\n"
        "Provide clear explanations, study tips, and learning strategies.\n"
        "If the question is subject-specific, suggest consulting a specialist."
    )
)

study_tips_agent = Agent(
    name="Study Tips Coach",
    instructions=(
        "You provide study techniques and learning strategies.\n"
        "Focus on: Time management, Active recall, Spaced repetition\n"
        "Recommend tools like Anki, Notion, Quizlet\n"
        "Help students develop effective study habits."
    )
)

# Specialized Agents
formatting_agent = Agent(
    name="Response Formatter",
    instructions=(
        "Format text to be readable while preserving all content:\n"
        "1. Break long paragraphs into shorter ones\n"
        "2. Use markdown for headings, lists, and emphasis\n"
        "3. Preserve $$LaTeX$$ math expressions\n"
        "4. Add spacing between sections\n"
        "5. Never change meaning or add content"
    ),
    model="gpt-3.5-turbo"
)

math_verification_agent = Agent(
    name="Math Verification",
    instructions=(
        "Verify mathematical content:\n"
        "1. Ensure all equations are properly formatted in $$LaTeX$$\n"
        "2. Check mathematical accuracy\n"
        "3. Flag potential errors\n"
        "4. Return verified content"
    )
)


def get_conversation_context(conversation_id: int) -> List[Dict]:
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    return [{"role": msg.role, "content": msg.content} for msg in messages]

def process_with_agents(user_message: str, conversation: Conversation) -> str:
    messages = get_conversation_context(conversation.id)
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Determine which agent to use
        if conversation.mode == "tutor":
            if conversation.sub_mode == "math":
                content = math_agent.generate_response(messages)
                content = math_verification_agent.generate_response(
                    [{"role": "user", "content": content}]
                )
            elif conversation.sub_mode == "english":
                content = english_agent.generate_response(messages)
            else:
                content = general_tutor_agent.generate_response(messages)
        else:  # study_tips
            content = study_tips_agent.generate_response(messages)
        
        # Final formatting
        formatted_content = formatting_agent.generate_response(
            [{"role": "user", "content": content}]
        )
        
        return formatted_content
        
    except Exception as e:
        print(f"Error in agent processing: {e}")
        return "I encountered an error processing your request. Please try again."




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
            "mode": conv.mode,
            "sub_mode": conv.sub_mode,
            "created_at": conv.created_at.isoformat(),
            "last_activity": last_activity.isoformat() if last_activity else conv.created_at.isoformat()
        } for conv, last_activity in conversations])
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return jsonify({"error": "Failed to fetch conversations"}), 500
    

@chat_bp.route("/conversations", methods=["POST"], endpoint="create_conversation")
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    data = request.json
    mode = data.get('mode')
    sub_mode = data.get('sub_mode')
    
    valid_modes = {
        'tutor': ['math', 'english', 'general'],
        'study_tips': []
    }
    
    if not mode or mode not in valid_modes:
        return jsonify({"error": "Invalid mode"}), 400
    if mode == 'tutor' and (not sub_mode or sub_mode not in valid_modes['tutor']):
        return jsonify({"error": "Invalid tutor type"}), 400

    try:
        # Create descriptive title
        if mode == 'tutor':
            title = f"Tutor - {sub_mode.capitalize()}"
        else:
            title = "Study Tips"
        
        new_conversation = Conversation(
            user_id=user_id,
            title=title,
            mode=mode,
            sub_mode=sub_mode if mode == 'tutor' else None
        )
        db.session.add(new_conversation)
        db.session.flush()
        
        # Add system message based on mode
        if mode == 'tutor':
            system_content = {
                'math': math_agent.instructions,
                'english': english_agent.instructions,
                'general': general_tutor_agent.instructions
            }[sub_mode]
        else:
            system_content = study_tips_agent.instructions
            
        system_message = Message(
            conversation_id=new_conversation.id,
            content=system_content,
            role="system"
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            "id": new_conversation.id,
            "title": new_conversation.title,
            "mode": new_conversation.mode,
            "sub_mode": new_conversation.sub_mode
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
    
    conversation = Conversation.query.filter_by(
        id=conversation_id, 
        user_id=user_id
    ).first_or_404()
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            content=user_message,
            role="user",
            created_at=datetime.utcnow()
        )
        db.session.add(user_msg)
        
        # Process with agent pipeline
        ai_response = process_with_agents(user_message, conversation)
        
        # Save AI response
        ai_msg = Message(
            conversation_id=conversation_id,
            content=ai_response,
            role="assistant",
            created_at=datetime.utcnow()
        )
        db.session.add(ai_msg)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "response": ai_response,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500