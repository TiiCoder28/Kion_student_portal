<template>
  <div class="dashboard-container">
    <!-- Sidebar -->
    <div class="sidebar">
      <img src="../assets/images/kion-robot.png" alt="Kion Logo" class="logo" />
      <div class="user-info">
        <div class="user-avatar">
          <img src="../assets/images/student-avatar.jpeg" alt="User" />
        </div>
        <div class="username">User name</div>
      </div>
      <div class="chat-history">
        <h3>Chat History</h3>
        <div 
          v-for="(chat, index) in chatHistory" 
          :key="index" 
          class="history-item"
          :class="{ active: currentChat === index }"
          @click="loadChat(index)"
        >
          {{ chat.title }}
        </div>
        <div class="new-chat-btn" @click="startNewChat">
          <span>+ New Chat</span>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="main-content">
      <div class="chat-container">
        <div class="chat-messages">
          <div v-for="(message, index) in messages" :key="index" class="message-container">
            <div :class="['message', message.sender === 'ai' ? 'ai-message' : 'user-message']">
              <div class="avatar">
                <img 
                  :src="message.sender === 'ai' ? '../assets/images/kion-robot.png' : '../assets/images/student-avatar.png'" 
                  :alt="message.sender === 'ai' ? 'AI Assistant' : 'User'" 
                />
              </div>
              <div class="message-content">{{ message.text }}</div>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <div class="input-container">
            <input 
              type="text" 
              v-model="userInput" 
              placeholder="Type your message here..." 
              @keyup.enter="sendMessage"
            />
            <div class="input-actions">
              <button class="action-btn">
                <img src="../assets/images/emoji-icon.jpeg" alt="Emoji" />
              </button>
              <button class="send-btn" @click="sendMessage">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000"; 

const userInput = ref("");
const currentChat = ref(0);
const messages = reactive([
    {
        sender: "ai",
        text: "Hello! I'm your Kion Student Assistant. How can I help you today?"
    }
]);

const chatHistory = reactive([
    { title: "Assignment Help", date: "Mar 12, 2025", type: "assignment_help", session_id: "assignment_help_1" },
    { title: "Study Tips", date: "Mar 8, 2025", type: "study_tips", session_id: "study_tips_1" }
]);

const sendMessage = async () => {
    if (userInput.value.trim() === "") return;

    // Add user message
    messages.push({
        sender: "user",
        text: userInput.value
    });

    const userQuestion = userInput.value;
    userInput.value = "";

    try {
        const response = await axios.post(
            `${API_BASE_URL}/api/chat`, 
            { 
                message: userQuestion,
                chat_type: chatHistory[currentChat.value].type,  // Pass the chat type
                session_id: chatHistory[currentChat.value].session_id  // Pass the session ID
            },
            { headers: { "Content-Type": "application/json" } } 
        );

        // Add AI response to chat
        if (response.data.response) {
            messages.push({
                sender: "ai",
                text: response.data.response
            });
        } else {
            messages.push({
                sender: "ai",
                text: "I didn't quite get that, can you try again?"
            });
        }

        scrollToBottom();
    } catch (error) {
        console.error("Error communicating with AI backend:", error.response?.data || error.message);
        messages.push({
            sender: "ai",
            text: "Sorry, I encountered an issue processing your request."
        });
    }
};

const scrollToBottom = () => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
};

const startNewChat = () => {
    // Clear messages and start a new chat
    messages.splice(0, messages.length);
    messages.push({
        sender: "ai",
        text: "Hello! I'm your Kion Student Assistant. How can I help you today?"
    });

    // Add new chat to history
    const newSessionId = `new_session_${Date.now()}`;  // Generate a unique session ID
    chatHistory.unshift({
        title: "New Conversation",
        date: new Date().toLocaleDateString(),
        type: "assignment_help",  // Default to assignment help
        session_id: newSessionId
    });

    currentChat.value = 0;
};

const loadChat = (index) => {
    currentChat.value = index;
    // In a real app, you would load the chat messages from storage/API
    // For demo, we'll just show a notification message
    messages.splice(0, messages.length);
    messages.push({
        sender: "ai",
        text: `Loading previous conversation: ${chatHistory[index].title}`
    });
};

onMounted(() => {
    scrollToBottom();
});
</script>

  
  <style scoped>
  .dashboard-container {
    display: flex;
    height: 100vh;
    background-color: #f9f9f9;
  }
  
  .sidebar {
    width: 280px;
    background-color: #1b408d;
    color: white;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }
  
  .logo {
    width: 100px;
    height: auto;
    margin-bottom: 30px;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    margin-bottom: 30px;
  }
  
  .user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    overflow: hidden;
    margin-right: 10px;
    background-color: #ffffff;
  }
  
  .user-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .user-name {
    font-weight: bold;
  }
  
  .chat-history {
    flex: 1;
    overflow-y: auto;
  }
  
  .chat-history h3 {
    margin-bottom: 15px;
    font-size: 16px;
    opacity: 0.8;
  }
  
  .history-item {
    padding: 10px;
    margin-bottom: 5px;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .history-item:hover, .history-item.active {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .new-chat-btn {
    margin-top: 15px;
    padding: 10px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    cursor: pointer;
    text-align: center;
    transition: background-color 0.2s;
  }
  
  .new-chat-btn:hover {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    background: linear-gradient(135deg, #0a1e4a, #1b408d);
    background-size: cover;
    position: relative;
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
  }
  
  .message-container {
    margin-bottom: 20px;
    max-width: 80%;
  }
  
  .ai-message {
    align-self: flex-start;
  }
  
  .user-message {
    align-self: flex-end;
    margin-left: auto;
  }
  
  .message {
    display: flex;
    align-items: flex-start;
  }
  
  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    overflow: hidden;
    margin-right: 10px;
    background-color: #ffffff;
    flex-shrink: 0;
  }
  
  .avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .message-content {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }
  
  .ai-message .message-content {
    background-color: #ffffff;
    color: #333;
  }
  
  .user-message .message-content {
    background-color: #24b9f9;
    color: white;
  }
  
  .chat-input {
    margin-top: 20px;
  }
  
  .input-container {
    display: flex;
    align-items: center;
    background-color: white;
    border-radius: 10px;
    padding: 5px 15px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .input-container input {
    flex: 1;
    border: none;
    padding: 12px 0;
    font-size: 14px;
    outline: none;
  }
  
  .input-actions {
    display: flex;
    align-items: center;
  }
  
  .action-btn {
    background: none;
    border: none;
    cursor: pointer;
    margin-right: 10px;
    opacity: 0.6;
    transition: opacity 0.2s;
  }
  
  .action-btn:hover {
    opacity: 1;
  }
  
  .action-btn img {
    width: 20px;
    height: 20px;
  }
  
  .send-btn {
    background-color: #24b9f9;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .send-btn:hover {
    background-color: #1da7e6;
  }
  </style>