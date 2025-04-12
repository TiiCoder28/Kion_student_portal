📚 Student Portal – AI-Powered Learning Assistant
Welcome to the Student Portal, an AI-driven learning companion designed for students across primary, high school, and university levels. The platform provides a personalized experience with friendly virtual tutors that help students with subjects like Math, English, and General Academic Support, along with useful Study Tips. ✨

🚀 Features
🔐 User Authentication: Secure login and sign-up with JWT

🧠 AI-Powered Tutors: Specialized bots for CAPS-aligned Math and English, plus general subjects

🎓 Study Coach: Recommends productivity tools and study techniques

💬 Chat History: Saves and manages previous conversations

📄 Document Support: Upload PDFs for content-based interactions (coming soon!)

🌐 Responsive Frontend: Built with Vue.js, styled using plain CSS

🛡️ Role-based guidance: Age-appropriate prompts and responses

🛠 Tech Stack
Layer	Technology
Frontend	Vue.js, Vite, Plain CSS
Backend	Flask, Python
AI Models	OpenAI GPT-4 (via API)
Database	PostgreSQL
Authentication	JWT (Flask-JWT-Extended)
⚙️ Setup Instructions
1. Clone the Repository


git clone https://github.com/your-username/student-portal.git
cd student-portal
2. Set Up the Backend


cd backend
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
3. Environment Variables
Create a .env file in the backend folder:

env


FLASK_APP=main.py
FLASK_ENV=development
OPENAI_API_KEY=your_openai_key
JWT_SECRET_KEY=your_jwt_secret_key
DATABASE_URL=postgresql://username:password@localhost:5432/student_portal


4. Initialize the Database
bash
Copy
Edit
flask db init
flask db migrate
flask db upgrade


5. Start the Backend Server

flask run


6. Set Up the Frontend

cd frontend
npm install
npm run dev
🧪 Testing
Basic tests can be added using pytest for the backend and vitest or jest for the frontend.

📄 Folder Structure
student-portal/
├── backend/
│   ├── app/
│   ├── auth/
│   ├── chat/
│   ├── database/
│   └── main.py
├── frontend/
│   ├── src/
│   ├── components/
│   ├── views/
│   └── App.vue
🤝 Contribution
Feel free to fork, clone, and contribute! Please open a PR if you’d like to add a feature or fix something.

📬 Contact
For support or questions: Tiisetso Khumalo
📧 tiisetso@kion.co.za
🌍 Based in South Africa

