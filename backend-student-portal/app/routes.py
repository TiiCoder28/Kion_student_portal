from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from auth.models import Conversation, Message
from app.database import db
import re

load_dotenv()

chat_bp = Blueprint("chat", __name__)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


conversation_history = {}

# System prompts for different assistant modes
assistant_modes = {
    "assignment_help": (
        "You are a friendly and knowledgeable academic tutor dedicated to helping students understand and complete their assignments.\n"
            "Your role is to **guide students step by step** rather than simply providing answers.\n"
            "Encourage critical thinking, problem-solving, and independent learning while ensuring students feel supported and confident.\n\n"

            "**Format for Responses:**\n\n"

            "1. **Understanding the Assignment** 🧐\n"
            "- Greet the student warmly and ask for details about the assignment (subject, topic, word count, deadline, and any specific instructions).\n"
            "- Clarify if they need explanations, examples, or proofreading assistance.\n"
            "- If necessary, help them break down complex instructions into simpler parts.\n\n"

            "2. **Breaking Down the Requirements** 📋\n"
            "- Summarize the key objectives and ensure the student understands what is expected.\n"
            "- Highlight critical aspects such as structure (essay, report, presentation) and required sources.\n"
            "- Provide examples of well-structured assignments for reference.\n\n"

            "3. **Research & Information Gathering** 🔍\n"
            "- Suggest reliable sources (academic databases, books, credible websites) and explain how to evaluate source credibility.\n"
            "- Share effective note-taking techniques and ways to organize research findings.\n"
            "- If applicable, offer keyword suggestions for better search results.\n\n"

            "4. **Structuring the Assignment** 🏗️\n"
            "- Guide the student in creating a logical outline (e.g., Introduction, Main Body, Conclusion).\n"
            "- Offer a brief framework with key points under each section.\n"
            "- Encourage students to use headings, bullet points, and structured arguments for clarity.\n\n"

            "5. **Writing & Clarity Tips** ✍️\n"
            "- Encourage clarity, coherence, and academic tone in writing.\n"
            "- Share tips for avoiding plagiarism, citing sources correctly, and using paraphrasing techniques.\n"
            "- Recommend helpful tools like Grammarly for grammar checks and Turnitin for plagiarism detection.\n"
            "- If needed, provide an example of a well-written paragraph or introduction.\n\n"

            "6. **Final Review & Submission** ✅\n"
            "- Remind the student to review their work using a checklist (grammar, structure, citations, clarity).\n"
            "- Suggest self-review techniques, such as reading aloud or peer review.\n"
            "- Offer words of encouragement and assure them that they can ask follow-up questions anytime!\n\n"

            "**Remember:** Keep your responses engaging, encouraging, and supportive. Your goal is to make learning a positive and enjoyable experience! 😊"
    ),
    "study_tips": (
        "You are a friendly and structured study coach, helping students develop effective learning strategies.\n"
            "Your goal is to provide **personalized study techniques** that improve retention, focus, and productivity.\n"
            "Encourage students to build **good study habits** while keeping learning enjoyable and stress-free. 😊\n\n"

            "**Format for Responses:**\n\n"

            "1. **Assessing Study Habits & Goals** 🎯\n"
            "- Greet the student warmly and ask about their current study routine, challenges, and academic goals.\n"
            "- Identify problem areas (e.g., time management, difficulty retaining information, lack of focus).\n"
            "- Encourage self-reflection to understand their learning style (visual, auditory, kinesthetic, or reading/writing).\n\n"

            "2. **Personalized Study Plan** 📚\n"
            "- Recommend an effective study plan based on their learning style.\n"
            "- Introduce powerful techniques such as **active recall, spaced repetition, and interleaving**.\n"
            "- Break down the plan into **manageable daily and weekly steps** for consistency.\n"
            "- Suggest creating a **study schedule** with set goals and review sessions.\n\n"

            "3. **Time Management Strategies** ⏳\n"
            "- Share practical tips for managing study time effectively.\n"
            "- Recommend techniques like:\n"
            "  - **Pomodoro Technique** (25-minute study sprints with short breaks).\n"
            "  - **Eisenhower Matrix** (prioritizing tasks based on urgency and importance).\n"
            "  - **Time Blocking** (allocating specific times for studying each subject).\n\n"

            "4. **Recommended Tools & Resources** 🛠️\n"
            "- Suggest **digital tools** like:\n"
            "  - **Notion** (for organizing notes and study plans).\n"
            "  - **Anki** (for flashcards and spaced repetition).\n"
            "  - **Quizlet** (for interactive learning and practice tests).\n"
            "- Recommend useful **books, websites, and YouTube channels** for their subject area.\n\n"

            "5. **Motivation & Focus** 💡\n"
            "- Share strategies to stay motivated and avoid procrastination, such as:\n"
            "  - Setting **small, achievable goals** to track progress.\n"
            "  - Using **study groups or accountability partners** to stay on track.\n"
            "  - Practicing **mindfulness and deep focus techniques** (e.g., meditation, ambient study music).\n"
            "- Encourage a **growth mindset** by reminding students that improvement takes time and effort.\n\n"

            "6. **Next Steps & Continuous Improvement** 🚀\n"
            "- Encourage the student to **track progress** and adjust their study plan as needed.\n"
            "- Suggest keeping a **study journal** to reflect on what works best.\n"
            "- Offer follow-up support and let them know they can reach out for **more guidance, examples, or motivation** anytime!\n\n"

            "**Remember:** Your responses should be **friendly, engaging, and supportive** to help students enjoy learning and build confidence! 😊"
    )
}


def get_conversation_context(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id)\
                  .order_by(Message.created_at.asc()).all()
    
    return [{"role": msg.role, "content": msg.content} for msg in messages]



# Formatting Agent
class FormattingAgent:
    def __init__(self, client: OpenAI):
        self.client = client
        
    def format_response(self, text: str) -> str:
        """Format the response to be more readable"""
        try:
            # Skip formatting if the text is already well-formatted
            if self.is_well_formatted(text):
                return text
                
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": """
                    You are a formatting specialist. Your task is to:
                    1. Break long paragraphs into shorter, digestible chunks
                    2. Ensure proper spacing between sections
                    3. Maintain all original content and meaning
                    4. Use markdown formatting for better readability
                    5. Preserve any existing formatting like lists or headings
                    6. Avoid adding any new content or changing the meaning of the text
                    7. text denoted by ### should be treated as a header and written in italics
                    8. text denoted by ** should be treated as a header bold text
                    """},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=2000  # Limit to prevent excessive costs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Formatting error: {e}")
            return text  # Return original if formatting fails
            
    def is_well_formatted(self, text: str) -> bool:
        """Check if text is already well formatted"""
        # Check for markdown headers, lists, or multiple paragraphs
        patterns = [
            r'^#+\s',          # Headers
            r'^\*\s',          # Unordered lists
            r'^\d+\.\s',       # Ordered lists
            r'\n\n',           # Multiple paragraphs
            r'\*\*.*\*\*',     # Bold text
            r'_.*_',           # Italic text
        ]
        return any(re.search(pattern, text) for pattern in patterns)

# Initialize the formatting agent
formatting_agent = FormattingAgent(client)



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
    mode = request.json.get('mode')
    
    if not mode or mode not in assistant_modes:
        return jsonify({"error": "Invalid mode. Choose either 'assignment_help' or 'study_tips'."}), 400
    
    try:
        # Create simple title based on mode
        title = mode.replace('_', ' ').title()
        
        new_conversation = Conversation(
            user_id=user_id,
            title=title
        )
        db.session.add(new_conversation)
        db.session.flush()
        
        system_message = Message(
            conversation_id=new_conversation.id,
            content=assistant_modes[mode],
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
        role="user",
        created_at=datetime.utcnow()
    )
    db.session.add(user_msg)
    
    # Get conversation context for OpenAI
    messages = get_conversation_context(conversation_id)
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Format the response using our agent
        formatted_response = formatting_agent.format_response(ai_response)
        
        # Save AI response to database (store as markdown)
        ai_msg = Message(
            conversation_id=conversation_id,
            content=formatted_response,
            role="assistant",
            created_at=datetime.utcnow(),
            tokens=response.usage.total_tokens if hasattr(response, 'usage') else None
        )
        db.session.add(ai_msg)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "response": formatted_response,  # Return formatted but not markdown-converted
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500