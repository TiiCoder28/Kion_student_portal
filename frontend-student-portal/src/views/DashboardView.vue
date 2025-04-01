<template>
  <div class="dashboard-container">
    <!-- Sidebar -->
    <div class="sidebar">
      <img src="../assets/images/kion-robot.png" alt="Kion Logo" class="logo" />
      <div class="user-info">
        <div class="user-avatar">
          <img src="../assets/images/student-avatar.jpeg" alt="User" />
        </div>
        <h3 class="username">Welcome {{ user.firstName }} 👋!</h3>
      </div>
      <div class="chat-history">
        <h3>Chat History</h3>
        <div 
          v-for="conversation in conversations" 
          :key="conversation.id" 
          class="history-item"
          :class="{ active: activeConversationId === conversation.id }"
          @click="loadConversation(conversation.id)"
        >
          {{ conversation.title }}
        </div>
        <div class="new-chat-btn" @click="startNewConversation">
          <span>+ New Chat</span>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="main-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading conversation...</p>
      </div>
      
      <div v-else class="chat-container">
        <div class="chat-messages">
          <div v-for="(message, index) in messages" :key="index" class="message-container">
            <div :class="['message', message.role === 'assistant' ? 'ai-message' : 'user-message']">
              <div class="avatar">
                <img 
                  :src="message.role === 'assistant' ? '../assets/images/kion-robot.png' : '../assets/images/student-avatar.png'" 
                  :alt="message.role === 'assistant' ? 'AI Assistant' : 'User'" 
                />
              </div>
              <div class="message-content">{{ message.content }}</div>
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
              :disabled="!activeConversationId"
              ref="messageInput"
            />
            <div class="input-actions">
              <button class="action-btn">
                <img src="../assets/images/emoji-icon.jpeg" alt="Emoji" />
              </button>
              <button class="send-btn" @click="sendMessage" :disabled="!activeConversationId">
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
import { ref, reactive, onMounted, nextTick } from "vue";
import axios from "axios";
import apiClient from "@/api/client.js";
import { useRouter } from "vue-router";

const API_BASE_URL = "http://localhost:5000";
const router = useRouter();
const userInput = ref("");
const messageInput = ref(null);

// User data
const user = reactive({
  firstName: "",
  lastName: "",
  email: ""
});

// Chat state
const loading = ref(false);
const activeConversationId = ref(null);
const messages = reactive([]);
const conversations = reactive([]);

// Format date for display
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// Fetch user data
const fetchUserData = async () => {
  try {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const response = await axios.get(`${API_BASE_URL}/auth/user`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    user.firstName = response.data.first_name;
    user.lastName = response.data.last_name;
    user.email = response.data.email;
  } catch (error) {
    console.error("Error fetching user data:", error);
    router.push("/login");
  }
};

// Fetch all conversations for the user
const fetchConversations = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem("access_token");
    const response = await axios.get(`${API_BASE_URL}/api/conversations`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    conversations.splice(0, conversations.length, ...response.data);
    
    // Load the most recent conversation by default
    if (conversations.length > 0) {
      await loadConversation(conversations[0].id);
    }
  } catch (error) {
    console.error("Error fetching conversations:", error);
  } finally {
    loading.value = false;
  }
};

// Load a specific conversation
const loadConversation = async (conversationId) => {
  try {
    loading.value = true;
    activeConversationId.value = conversationId;
    const token = localStorage.getItem("access_token");
    
    const response = await axios.get(`${API_BASE_URL}/api/conversations/${conversationId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    messages.splice(0, messages.length, ...response.data.messages.filter(m => m.role !== 'system'));
    scrollToBottom();
  } catch (error) {
    console.error("Error loading conversation:", error);
  } finally {
    loading.value = false;
  }
};

// Create a new conversation
const startNewConversation = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem("access_token");
    
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations`,
      { mode: "assignment_help" },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    
    // Add new conversation to the top of the list
    conversations.unshift(response.data);
    await loadConversation(response.data.id);
    
    nextTick(() => {
      if (messageInput.value) {
        messageInput.value.focus();
      }
    });

  } catch (error) {
    console.error("Error creating conversation:", error);
  } finally {
    loading.value = false;
  }
};

// Send a message
const sendMessage = async () => {
  if (!userInput.value.trim() || !activeConversationId.value) return;

  try {
    const token = localStorage.getItem("access_token");
    const messageContent = userInput.value;
    
    // Add user message to UI immediately
    messages.push({
      role: "user",
      content: messageContent,
      created_at: new Date().toISOString()
    });
    
    userInput.value = "";
    scrollToBottom();
    
    // Send to backend
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations/${activeConversationId.value}/chat`,
      { message: messageContent },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );
    
    // Add AI response
    messages.push({
      role: "assistant",
      content: response.data.response,
      created_at: new Date().toISOString()
    });
    
    // Refresh conversation list to update timestamps
    await fetchConversations();
    scrollToBottom();
  } catch (error) {
    console.error("Error sending message:", error);
    messages.push({
      role: "assistant",
      content: "Sorry, I encountered an error processing your request.",
      created_at: new Date().toISOString()
    });
  }
};

// Helper function to scroll to bottom of chat
const scrollToBottom = () => {
  nextTick(() => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
      });
    }
  });
};

// Initialize component
onMounted(async () => {
  nextTick(() => {
    if(messageInput.value) {
      messageInput.value.focus();
    }
  });
  await fetchUserData();
  await fetchConversations();
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
    max-height: calc(100vh - 200px);

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
    max-height: calc(100vh - 180px); /* Adjust based on your input height */
  scroll-behavior: smooth
  }
  
  .message-container {
    margin-bottom: 10px;
    width: 100%;
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

.chat-history::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
  </style>