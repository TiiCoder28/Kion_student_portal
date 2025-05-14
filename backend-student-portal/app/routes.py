from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from auth.models import Conversation, Message
from app.database import db
import re
from typing import List, Dict, Optional
from auth.models import User
import json

load_dotenv()

chat_bp = Blueprint("chat", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


conversation_history = {}

class Agent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4o-mini",
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
        "You're a friendly and patient math tutor for South African students from primary school to university.\n"
        "PEDAGOGICAL APPROACH:\n"
        "1. Always start by assessing the student's current understanding\n"
        "2. Break concepts into small, manageable steps\n"
        "3. Use the Socratic method - ask guiding questions rather than giving direct answers\n"
        "4. Provide real-world examples relevant to South African context\n"
        "\n"
        "FORMATTING:\n"
        "- Inline math: $E=mc^2$\n"
        "- Display math: $$\\frac{1}{2} + \\frac{1}{4} = \\frac{3}{4}$$\n"
        "- Vectors: $\\vec{v}$ or $\\mathbf{v}$\n"
        "- Matrices: $\\begin{pmatrix}1 & 2\\\\3 & 4\\end{pmatrix}$\n"
        "\n"
        "RESPONSE STRUCTURE:\n"
        "1. Personalized greeting using student's name\n"
        "2. Restate the problem in your own words to confirm understanding\n"
        "3. Guide through solution with questions\n"
        "4. Provide final answer only after student attempts\n"
        "5. End with a challenge question to reinforce learning\n"
        "\n"
    )
)

english_agent = Agent(
    name="English Helper (CAPS-Aligned)",
    instructions=(
        "You're a warm and supportive English tutor for South African students, from primary school to university.\n"
        "ALWAYS refer to the student by name at the beginning of your response if their name is available. "
        "For example: 'Hi ${user.first_name}! ✨ Let's learn about English together!'\n"
        "Or whenever you answer the student's question use their name\n"
        "For example: 'Great question, ${user.first_name}!'\n"
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
    name="Holistic Learning Guide",
    instructions=(
        "You're a versatile tutor helping with multiple subjects across the South African curriculum.\n"
        "TUTORING STRATEGY:\n"
        "1. Start by identifying the student's learning style (visual, auditory, kinesthetic)\n"
        "2. Adapt explanations accordingly\n"
        "3. Connect new concepts to prior knowledge\n"
        "4. Use the 'I do, we do, you do' scaffolding approach\n"
        "\n"
        "CROSS-CURRICULAR CONNECTIONS:\n"
        "- Show how math applies to geography (e.g., map scales)\n"
        "- Connect history to current events\n"
        "- Relate science to everyday life in South Africa\n"
        "\n"
        "RESPONSE TEMPLATE:\n"
        "1. Warm greeting using student's name\n"
        "2. Diagnostic question to gauge understanding\n"
        "3. Explanation with appropriate scaffolding\n"
        "4. Check for understanding with a quick question\n"
        "5. Suggest additional resources\n"
        "\n"
    )
)

history_agent = Agent(
    name="History Helper (CAPS-Aligned)",
    instructions=(
        "You're an engaging history tutor for South African students.\n"
        "ALWAYS refer to the student by name at the beginning of your response if available.\n"
        "Example: 'Hi {user.first_name}! Let's explore history together!'\n\n"
        "📚 Cover: Ancient civilizations, SA history, World Wars, Apartheid, Democracy\n"
        "🌍 Connect historical events to modern contexts\n"
        "📅 Use timelines and cause/effect explanations\n"
        "🧭 Highlight diverse perspectives and primary sources\n"
        "✨ Make history come alive with stories and relevance to students' lives"
    )
)

geography_agent = Agent(
    name="Geography Helper (CAPS-Aligned)",
    instructions=(
        "You're an enthusiastic geography tutor for South African students.\n"
        "ALWAYS use the student's name if available.\n"
        "Example: 'Hello {user.first_name}! Ready to explore our world?'\n\n"
        "🗺️ Cover: Physical geography, Human geography, Map skills, SA regions\n"
        "🌦️ Explain weather systems and climate change\n"
        "🏙️ Discuss urbanization and settlement patterns\n"
        "🌱 Teach about ecosystems and sustainability\n"
        "📊 Use maps, diagrams and real-world examples"
    )
)

physical_science_agent = Agent(
    name="Physical Science Helper (CAPS-Aligned)",
    instructions=(
        "You're an enthusiastic physical science tutor specializing in the South African CAPS curriculum.\n"
        "TEACHING METHODOLOGY:\n"
        "1. Always relate concepts to practical South African examples (e.g., energy to Eskom)\n"
        "2. Use the predict-observe-explain model for experiments\n"
        "3. Emphasize the scientific method in all explanations\n"
        "\n"
        "FORMATTING REQUIREMENTS:\n"
        "- Chemical formulas: $\\mathrm{H_2O}$\n"
        "- Units: $5\\,\\mathrm{kg}$ (never '5kg')\n"
        "- Vectors: $\\vec{F} = m\\vec{a}$\n"
        "- Temperatures: $30\\,^{\\circ}\\mathrm{C}$\n"
        "- Equations always on new line: $$\\vec{F} = \\frac{G m_1 m_2}{r^2}$$\n"
        "\n"
        "RESPONSE TEMPLATE:\n"
        "1. Concept explanation with real-world analogy\n"
        "2. Step-by-step derivation/solution\n"
        "3. Common misconceptions to watch for\n"
        "4. Practice question for reinforcement\n"
        "\n"
    )
)

study_tips_agent = Agent(
    name="Study Coach Pro",
    instructions=(
        "You're an expert study coach helping South African students develop effective learning strategies.\n"
        "COACHING FRAMEWORK:\n"
        "1. ASSESS: Ask about their current study habits\n"
        "2. DIAGNOSE: Identify key areas for improvement\n"
        "3. PRESCRIBE: Recommend specific techniques\n"
        "4. FOLLOW-UP: Check progress in next session\n"
        "\n"
        "EVIDENCE-BASED TECHNIQUES TO PROMOTE:\n"
        "- Spaced repetition with Anki\n"
        "- Active recall through self-testing\n"
        "- Interleaving practice\n"
        "- Pomodoro technique (25/5)\n"
        "- Mind mapping for visual learners\n"
        "\n"
        "RESPONSE STRUCTURE:\n"
        "1. Personalized greeting\n"
        "2. Specific praise for what they're doing well\n"
        "3. One concrete suggestion for improvement\n"
        "4. Actionable steps they can take immediately\n"
        "5. Encouragement and motivation\n"
        "\n"
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
        "6. Do not respond, just return the correct format"
    )
)


def get_conversation_context(conversation_id: int) -> List[Dict]:
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    return [{"role": msg.role, "content": msg.content} for msg in messages]

def verify_science_content(content: str) -> str:
    """Special verification for science content"""
    patterns = [
        (r'\b\d+[a-zA-Z]+\b', lambda m: f"{m.group(0)[:-1]}\\,\\mathrm{{{m.group(0)[-1:]}}}"),  # 5kg -> 5\,\mathrm{kg}
        (r'\d+\s*°\s*[CF]', lambda m: f"{m.group(0).split('°')[0]}\\,^{{\\circ}}\\mathrm{{{m.group(0)[-1:]}}}")  # 30°C -> 30\,^{\circ}\mathrm{C}
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content

def process_with_agents(user_message: str, conversation: Conversation, user: User) -> str:
    messages = get_conversation_context(conversation.id)
    
    # Remove the original system message if it exists
    messages = [msg for msg in messages if msg['role'] != 'system']
    
    # Add the user message
    messages.append({"role": "user", "content": user_message})
    
    try:
        # Determine which agent to use
        if conversation.mode == "tutor":
            agent_map = {
                "math": math_agent,
                "english": english_agent,
                "general": general_tutor_agent,
                "history": history_agent,
                "geography": geography_agent,
                "physical_science": physical_science_agent
            }
            agent = agent_map.get(conversation.sub_mode, general_tutor_agent)
        else:
            agent = study_tips_agent
            
        first_name = user.first_name if user and user.first_name else None
        system_message = {
            "role": "system",
            "content": f"Current user's name: {first_name}\n\n{agent.instructions}"
        }
        
        messages.insert(0, system_message)
        content = agent.generate_response(messages[1:])
        
        # For math and science, verify the response
        if conversation.mode == "tutor" and conversation.sub_mode in ["math", "physical_science"]:
            content = verify_science_content(content)
            verification_prompt = (
               "Please verify and correct ONLY the mathematical/scientific expressions in the following text. "
               "Focus on:\n"
               "1. Proper LaTeX formatting\n"
               "2. Correct scientific notation\n"
               "3. Appropriate unit formatting\n"
               "4. Vector notation\n\n"
               "Text to verify:\n\n" + content +
               "Do not change any other part of the response. "
               "If all is correct, return the exact same text. "
               "If there are errors, correct them using LaTeX formatting.\n\n"
               "Here's the text to verify:\n\n" + content
            )
            
            verified_content = math_verification_agent.generate_response(
                [{"role": "user", "content": verification_prompt}]
            )
            content = verified_content

        if conversation.mode == "tutor" and conversation.sub_mode == "math" or conversation.sub_mode == "physical_science":
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
    

@chat_bp.route("/conversations", methods=["POST"])
@jwt_required()
def create_conversation():
    user_id = get_jwt_identity()
    data = request.json
    mode = data.get('mode')
    sub_mode = data.get('sub_mode')
    
    valid_modes = {
        'tutor': ['math', 'english', 'general', 'history', 'geography', 'physical_science'],
        'study_tips': []
    }
    
    if not mode or mode not in valid_modes:
        return jsonify({"error": "Invalid mode"}), 400
    if mode == 'tutor' and (not sub_mode or sub_mode not in valid_modes['tutor']):
        return jsonify({"error": "Invalid tutor type"}), 400

    try:
        # Check for existing active conversation in this mode/sub_mode
        existing = Conversation.query.filter_by(
            user_id=user_id,
            mode=mode,
            sub_mode=sub_mode if mode == 'tutor' else None,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({
                "error": "You already have an active conversation in this mode",
                "existing_conversation_id": existing.id
            }), 400

        # Create descriptive title
        title_map = {
            'math': "Mathematics Tutor",
            'english': "English Tutor",
            'general': "General Tutor",
            'history': "History Tutor",
            'geography': "Geography Tutor",
            'physical_science': "Physical Science Tutor"
        }
        title = title_map.get(sub_mode, "Tutor Session") if mode == 'tutor' else "Study Tips"
        
        new_conversation = Conversation(
            user_id=user_id,
            title=title,
            mode=mode,
            sub_mode=sub_mode if mode == 'tutor' else None,
            is_active=True
        )
        db.session.add(new_conversation)
        db.session.flush()
        
        # Add system message based on mode
        agent_map = {
            'math': math_agent,
            'english': english_agent,
            'general': general_tutor_agent,
            'history': history_agent,
            'geography': geography_agent,
            'physical_science': physical_science_agent
        }

        system_content = agent_map.get(sub_mode, general_tutor_agent).instructions if mode == 'tutor' else study_tips_agent.instructions
            
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
    
    # Get user details from the database
    user = db.session.get(User, user_id)  # Using get() which is preferred in SQLAlchemy 2.0+
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    print(f"User object type: {type(user)}")
    print(f"User first_name: {getattr(user, 'first_name', 'NOT FOUND')}")
    
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
        
        # Process with agent pipeline - pass user object
        ai_response = process_with_agents(user_message, conversation, user)
        
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
            "formatted_response": format_response(ai_response),
            "conversation_id": conversation_id
        })
        
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500
    
@chat_bp.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id):
    user_id = get_jwt_identity()
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first_or_404()
        
        # Delete all messages first to maintain referential integrity
        Message.query.filter_by(conversation_id=conversation_id).delete()
        
        # Then delete the conversation
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({"message": "Conversation deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting conversation: {e}")
        return jsonify({"error": "Failed to delete conversation"}), 500
    
    
@chat_bp.route("/conversations/<int:conversation_id>/archive", methods=["POST"])
@jwt_required()
def archive_conversation(conversation_id):
    user_id = get_jwt_identity()
    try:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first_or_404()
        
        conversation.is_active = False
        db.session.commit()
        
        return jsonify({"message": "Conversation archived successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error archiving conversation: {e}")
        return jsonify({"error": "Failed to archive conversation"}), 500


@chat_bp.route("/conversations/archived", methods=["GET"])
@jwt_required()
def get_archived_conversations():
    user_id = get_jwt_identity()
    try:
        conversations = db.session.query(
            Conversation,
            db.func.max(Message.created_at).label('last_activity')
        ).join(Message)\
         .filter(
             Conversation.user_id == user_id,
             Conversation.is_active == False
         )\
         .group_by(Conversation.id)\
         .order_by(db.desc('last_activity'))\
         .limit(20)\
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
        print(f"Error fetching archived conversations: {e}")
        return jsonify({"error": "Failed to fetch archived conversations"}), 500
    

@chat_bp.route("/conversations/<int:conversation_id>/stream", methods=["POST"])
@jwt_required()
def stream_chat(conversation_id):
    user_id = get_jwt_identity()
    data = request.json
    user_message = data.get('message', '').strip()
    
    conversation = Conversation.query.filter_by(
        id=conversation_id, 
        user_id=user_id
    ).first_or_404()
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        content=user_message,
        role="user",
        created_at=datetime.utcnow()
    )
    db.session.add(user_msg)
    db.session.commit()
    
    def generate():
        try:
            messages = get_conversation_context(conversation.id)
            messages = [msg for msg in messages if msg['role'] != 'system']
            messages.append({"role": "user", "content": user_message})
            
            # Determine which agent to use
            if conversation.mode == "tutor":
                agent_map = {
                    "math": math_agent,
                    "english": english_agent,
                    "general": general_tutor_agent,
                    "history": history_agent,
                    "geography": geography_agent,
                    "physical_science": physical_science_agent
                }
                agent = agent_map.get(conversation.sub_mode, general_tutor_agent)
            else:
                agent = study_tips_agent
                
            first_name = user.first_name if user and user.first_name else None
            system_message = {
                "role": "system",
                "content": f"Current user's name: {first_name}\n\n{agent.instructions}"
            }
            
            messages.insert(0, system_message)
            
            # Create streaming response
            stream = client.chat.completions.create(
                model=agent.model,
                messages=messages[1:],
                temperature=0.3,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            # Save the full response
            ai_msg = Message(
                conversation_id=conversation_id,
                content=full_response,
                role="assistant",
                created_at=datetime.utcnow()
            )
            db.session.add(ai_msg)
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")