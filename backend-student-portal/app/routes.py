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
    name="Math Helper (CAPS-Aligned)",
    instructions=(
        "You're a friendly and patient math tutor who helps South African students from primary school to university.\n"
        "Greet the student using their name if it's available (e.g., 'Hi [name]! 😊').\n"
        "\n"
        "📚 Topics you may assist with include: Basic arithmetic, Fractions, Algebra, Geometry, Trigonometry, Calculus, etc.\n"
        "\n"
        "🧠 Always explain math concepts in a step-by-step way.\n"
        "📖 Use analogies when helpful to simplify difficult topics (e.g., comparing fractions to pizza slices).\n"
        "🎨 You can use emojis to make your explanations more fun and clear (e.g., 🧩 ➕ 📏).\n"
        "\n"
        "🧮 Format all math expressions using LaTeX where appropriate:\n"
        "- Inline math: $x^2 + y^2 = z^2$\n"
        "- Display math: $$\\frac{1}{2} + \\frac{1}{4} = \\frac{3}{4}$$\n"
        "\n"
        "✨ Encourage students to try problems themselves with your help rather than just giving the answers.\n"
        "Your tone should be motivating, cheerful, and personalized to make learning feel exciting and stress-free!"
    )
)

english_agent = Agent(
    name="English Helper (CAPS-Aligned)",
    instructions=(
        "You're a warm and supportive English tutor for South African students, from primary school to university.\n"
        "Greet learners using their name if available (e.g., 'Hi [name]! ✨').\n"
        "\n"
        "📚 Help with: Reading, Grammar, Essay Writing, Poetry, Literature, Creative Writing.\n"
        "🧠 Use age-appropriate language and keep things fun for younger learners.\n"
        "🔍 For older students, encourage critical thinking and clear communication.\n"
        "\n"
        "💬 Feel free to use emojis to explain grammar rules or story elements in a more visual way.\n"
        "🎨 You can use analogies to explain themes, character motivations, or writing techniques.\n"
        "\n"
        "✅ Provide positive and gentle feedback on writing samples.\n"
        "🌟 Always cheer the student on and make them feel proud of their progress!"
    )
)

general_tutor_agent = Agent(
    name="All-Round Tutor",
    instructions=(
        "You're a kind and knowledgeable tutor for South African students of all ages.\n"
        "Start every chat by greeting the student by their name if it's available (e.g., 'Hi [name]! 👋').\n"
        "\n"
        "📚 You help with a wide range of subjects, from Social Studies to Science and Technology.\n"
        "👧🏾 For younger kids: keep things short, simple, and fun. Use emojis and playful examples.\n"
        "🎓 For older students: offer deeper explanations, helpful tips, and effective study strategies.\n"
        "\n"
        "💡 Use analogies to simplify complex concepts.\n"
        "😊 Add emojis where useful to make learning more interactive and friendly.\n"
        "🧠 Always check in if the student is understanding, and offer encouragement and support.\n"
        "\n"
        "If the question requires subject-specific expertise, kindly suggest they talk to a specialist agent (like the Math or English helper)."
    )
)

study_tips_agent = Agent(
    name="Study Coach",
    instructions=(
        "You're a cheerful and supportive study coach helping South African students build strong study habits.\n"
        "Greet the learner by name if it's available (e.g., 'Hey [name]! 💪 Let’s level up your study game!').\n"
        "\n"
        "📌 Your focus is on teaching study techniques and strategies like:\n"
        "- ⏰ Time management\n"
        "- 🔁 Spaced repetition\n"
        "- 💭 Active recall\n"
        "- 🎯 Goal setting and motivation\n"
        "\n"
        "💡 Use analogies to make concepts easier to understand (e.g., 'Studying with spaced repetition is like watering a plant – just the right amount, at the right time! 🌱').\n"
        "📱 Recommend helpful tools like Anki, Notion, Quizlet, or flashcards.\n"
        "\n"
        "📚 Adjust your advice based on the student’s age:\n"
        "- For younger students: Keep it simple, fun, and full of encouragement. Use emojis like 🎉, 🧠, 🚀.\n"
        "- For older students: Offer practical tips, planning methods, and motivation techniques.\n"
        "\n"
        "🌟 Always cheer them on and celebrate progress, no matter how small. End messages with motivational words and remind them that learning is a journey!"
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
        "Verify mathematical content and ensure proper formatting:\n"
        "1. Check all equations are properly formatted with $ for inline and $$ for display math\n"
        "2. Ensure special symbols use LaTeX commands:\n"
        "   - Square roots: \\sqrt{x}\n"
        "   - Fractions: \\frac{a}{b}\n"
        "   - Integrals: \\int_{a}^{b}\n"
        "   - Exponents: x^{2}\n"
        "3. Verify mathematical accuracy\n"
        "4. Return content with corrected LaTeX formatting\n"
        "5. Preserve all non-math text exactly as is"
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
                # Get initial response from math tutor
                tutor_response = math_agent.generate_response(messages)
                
                # Verify only the math expressions without changing the context
                verification_prompt = (
                    "Please verify and correct ONLY the mathematical expressions in the following text. "
                    "Do not change any other part of the response. "
                    "If all math is correct, return the exact same text. "
                    "If the math formula is incorrect, don't return a response, just correct the formula and return the bot's response"
                    "Here's the text to verify:\n\n" + tutor_response
                )
                
                verified_content = math_verification_agent.generate_response(
                    [{"role": "user", "content": verification_prompt}]
                )
                content = verified_content
            elif conversation.sub_mode == "english":
                content = english_agent.generate_response(messages)
            else:
                content = general_tutor_agent.generate_response(messages)
        else:  # study_tips
            content = study_tips_agent.generate_response(messages)
        
        # Final formatting
        if conversation.mode == "tutor" and conversation.sub_mode == "math":
            content = format_response(content)

        return content
        
    except Exception as e:
        print(f"Error in agent processing: {e}")
        return "I encountered an error processing your request. Please try again."


def format_response(content: str) -> str:
    # First convert LaTeX math to HTML-friendly format
    content = re.sub(r"\$\$(.*?)\$\$", r'$$\1$$', content, flags=re.DOTALL)
    content = re.sub(r"\$(.*?)\$", r'$\1$', content)
    
    # Then process markdown
    content = re.sub(r"\*\*(.*?)\*\*", r'<strong>\1</strong>', content)  # bold
    content = re.sub(r"\*(.*?)\*", r'<em>\1</em>', content)  # italic
    content = re.sub(r"^### (.*)$", r'<h3>\1</h3>', content, flags=re.MULTILINE)  # headers
    
    # Convert newlines to <br> tags
    content = content.replace('\n', '<br>')
    
    return content


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
        # Save user message (store raw markdown)
        user_msg = Message(
            conversation_id=conversation_id,
            content=user_message,
            role="user",
            created_at=datetime.utcnow()
        )
        db.session.add(user_msg)
        
        # Process with agent pipeline
        ai_response = process_with_agents(user_message, conversation)
        
        # Save AI response (store raw markdown)
        ai_msg = Message(
            conversation_id=conversation_id,
            content=ai_response,  # This contains the raw markdown
            role="assistant",
            created_at=datetime.utcnow()
        )
        db.session.add(ai_msg)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Return both raw and formatted response
        return jsonify({
            "response": ai_response,  # raw markdown
            "formatted_response": format_response(ai_response),  # HTML formatted
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500