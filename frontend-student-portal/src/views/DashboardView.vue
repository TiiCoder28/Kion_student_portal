<template>
  <div class="dashboard-container">
    <!-- Sidebar -->
    <div class="sidebar">
      <img src="../assets/images/kion-robot.png" alt="Kion Logo" class="logo" />
      <div class="user-info">
        <div class="user-avatar">
          <img src="../assets/images/student-avatar.jpeg" alt="User" />
        </div>
        <h1>Welcome, {{ user.first_name || 'User' }} {{ user.last_name || '' }}!</h1>
      </div>
      <div class="chat-history">
        <h3>Chat History</h3>
        
        <!-- Assignment Help Section -->
        <div class="dropdown-section">
          <div class="dropdown-header" @click="toggleDropdown('assignment')">
            Assignment Help
            <span class="dropdown-arrow">{{ openDropdown === 'assignment' ? '▲' : '▼' }}</span>
          </div>
          <div v-if="openDropdown === 'assignment'" class="dropdown-content">
            <div v-if="getChatsByType('assignment_help').length > 0">
              <div 
                v-for="(chat, index) in getChatsByType('assignment_help')" 
                :key="chat.id" 
                class="history-item"
                :class="{ active: currentChat?.id === chat.id }"
                @click="loadChat(chat.id)"
              >
                <div class="chat-info">
                  <div class="chat-title">{{ chat.title }}</div>
                  <div class="chat-date">{{ formatDate(chat.created_at) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="no-chats">
              No assignment help history
            </div>
            <button class="new-chat-btn" @click="startNewChat('assignment_help')">
              + New Assignment Chat
            </button>
          </div>
        </div>
        
        <!-- Study Tips Section -->
        <div class="dropdown-section">
          <div class="dropdown-header" @click="toggleDropdown('study')">
            Study Tips
            <span class="dropdown-arrow">{{ openDropdown === 'study' ? '▲' : '▼' }}</span>
          </div>
          <div v-if="openDropdown === 'study'" class="dropdown-content">
            <div v-if="getChatsByType('study_tips').length > 0">
              <div 
                v-for="(chat, index) in getChatsByType('study_tips')" 
                :key="chat.id" 
                class="history-item"
                :class="{ active: currentChat?.id === chat.id }"
                @click="loadChat(chat.id)"
              >
                <div class="chat-info">
                  <div class="chat-title">{{ chat.title }}</div>
                  <div class="chat-date">{{ formatDate(chat.created_at) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="no-chats">
              No study tips history
            </div>
            <button class="new-chat-btn" @click="startNewChat('study_tips')">
              + New Study Tips Chat
            </button>
          </div>
        </div>
        
        <!-- Essay Helper Section -->
        <div class="dropdown-section">
          <div class="dropdown-header" @click="toggleDropdown('essay')">
            Essay Helper
            <span class="dropdown-arrow">{{ openDropdown === 'essay' ? '▲' : '▼' }}</span>
          </div>
          <div v-if="openDropdown === 'essay'" class="dropdown-content">
            <div v-if="getChatsByType('essay_helper').length > 0">
              <div 
                v-for="(chat, index) in getChatsByType('essay_helper')" 
                :key="chat.id" 
                class="history-item"
                :class="{ active: currentChat?.id === chat.id }"
                @click="loadChat(chat.id)"
              >
                <div class="chat-info">
                  <div class="chat-title">{{ chat.title }}</div>
                  <div class="chat-date">{{ formatDate(chat.created_at) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="no-chats">
              No essay helper history
            </div>
            <button class="new-chat-btn" @click="startNewChat('essay_helper')">
              + New Essay Helper Chat
            </button>
          </div>
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
              :disabled="isLoading"
            />
            <div class="input-actions">
              <button class="action-btn">
                <img src="../assets/images/emoji-icon.jpeg" alt="Emoji" />
              </button>
              <button class="send-btn" @click="sendMessage" :disabled="isLoading">
                {{ isLoading ? 'Sending...' : 'Send' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import axios from "axios";
import { authAxios } from '../utils/auth'

const API_BASE_URL = "http://127.0.0.1:5000"; 

// Reactive state
const user = ref(JSON.parse(localStorage.getItem('user')) || {});
const userInput = ref("");
const currentChat = ref(null);
const messages = reactive([]);
const chatHistory = reactive([]);
const openDropdown = ref(null); // Track which dropdown is open
const isLoading = ref(false);


// Helper to filter chats by type
const getChatsByType = (type) => {
  return chatHistory.filter(chat => chat.type === type);
};

const toggleDropdown = (type) => {
  openDropdown.value = openDropdown.value === type ? null : type;
};

const formatDate = (dateString) => {
  const options = { month: 'short', day: 'numeric', year: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const getWelcomeMessage = (chatType) => {
  const welcomeMessages = {
    assignment_help: "Hello! I'm here to help with your assignments. What are you working on today?",
    study_tips: "Ready to improve your study habits? Let's discuss some effective strategies!",
    essay_helper: "I can help you plan and structure your essay. What's your topic?"
  };
  return welcomeMessages[chatType] || "Hello! I'm your Kion Student Assistant. How can I help you today?";
};

const startNewChat = async (chatType) => {
  openDropdown.value = null;
  messages.splice(0, messages.length);
  messages.push({
    sender: "ai",
    text: getWelcomeMessage(chatType)
  });

  const newSessionId = `session_${Date.now()}`;
  const newChat = {
    id: newSessionId,
    title: `${toTitleCase(chatType.replace('_', ' '))} - ${new Date().toLocaleDateString()}`,
    type: chatType,
    created_at: new Date().toISOString()
  };
  
  chatHistory.unshift(newChat);
  currentChat.value = newChat;
};

const toTitleCase = (str) => {
  return str.replace(/\w\S*/g, (txt) => {
    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
  });
};

const sendMessage = async () => {
  if (userInput.value.trim() === "" || isLoading.value) {
    return;
  }

  if (!currentChat.value) {
    // If no current chat, start a default one
    await startNewChat('assignment_help');
  }

  isLoading.value = true;
  const userMessage = {
    sender: "user",
    text: userInput.value
  };
  messages.push(userMessage);
  
  const messageToSend = userInput.value;
  userInput.value = "";

  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/chat`, 
      { 
        message: messageToSend,
        chat_type: currentChat.value.type,
        session_id: currentChat.value.id
      },
      { 
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`
        } 
      }
    );

    if (response.data.error) {
      throw new Error(response.data.error);
    }

    messages.push({
      sender: "ai",
      text: response.data.response
    });

    await fetchChatHistory();
    scrollToBottom();
  } catch (error) {
    console.error("Error sending message:", error);
    messages.push({
      sender: "ai",
      text: "Sorry, I encountered an issue processing your request. Please try again."
    });
  } finally {
    isLoading.value = false;
  }
};

const fetchChatHistory = async () => {
  try {
    const response = await authAxios.get('/api/chats')
    
    chatHistory.splice(0, chatHistory.length, ...response.data);
    
    if (chatHistory.length > 0 && !currentChat.value) {
      currentChat.value = chatHistory[0];
      await loadChat(chatHistory[0].id);
    }
    else if (chatHistory.length > 0 && !currentChat.value) {
      currentChat.value = chatHistory[0];
      await loadChat(chatHistory[0].id);
    }

  } catch (error) {
    if (error.response?.status === 401) {
      router.push('/login')
    }
  }
};

const loadChat = async (chatId) => {
  const chat = chatHistory.find(c => c.id === chatId);
  if (!chat) return;
  
  currentChat.value = chat;
  
  try {
    const response = await axios.get(`${API_BASE_URL}/api/chats/${chatId}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    });
    
    messages.splice(0, messages.length);
    response.data.forEach(msg => {
      messages.push({
        sender: msg.sender,
        text: msg.content
      });
    });
  } catch (error) {
    console.error("Error loading chat:", error);
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
};

onMounted(async () => {
  user.value = JSON.parse(localStorage.getItem('user')) || {};
  

  await fetchChatHistory();
});
</script>


  
  <style scoped>
  .dashboard-container {
    display: flex;
    height: 100vh;
    background-color: #f9f9f9;
  }

  h1 {
  font-size: 2rem;
  color: white;
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
  
  .dropdown-container {
  position: relative;
  margin-bottom: 15px;
}

.dropdown-btn {
  width: 100%;
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
  text-align: left;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-section {
  margin-bottom: 15px;
}

.dropdown-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.dropdown-arrow {
  font-size: 0.8em;
}

.dropdown-content {
  position: absolute;
  width: 100%;
  background-color: #1b408d;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  z-index: 1;
}

.dropdown-content div {
  padding: 10px;
  cursor: pointer;
}

.dropdown-content div:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.no-chats {
  padding: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
  text-align: center;
}

.new-chat-btn {
  width: 100%;
  padding: 8px;
  margin-top: 10px;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
}

.new-chat-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.history-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 5px;
  border-radius: 5px;
  cursor: pointer;
}

.chat-type-icon {
  margin-right: 10px;
  font-size: 1.2em;
}

.chat-info {
  flex: 1;
}

.chat-title {
  font-weight: 500;
}

.chat-date {
  font-size: 0.8em;
  opacity: 0.7;
}

/* Style different chat types differently */
.history-item.assignment-help {
  border-left: 3px solid #24b9f9;
}

.history-item.study-tips {
  border-left: 3px solid #4CAF50;
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

  .send-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.input-container input:disabled {
  background-color: #f0f0f0;
}
  </style>