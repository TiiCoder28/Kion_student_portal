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
        
        <!-- Today's Chats -->
        <div v-if="todaysConversations.length > 0" class="history-section">
          <h4 class="history-section-title">Today</h4>
          <div 
            v-for="conversation in todaysConversations" 
            :key="conversation.id" 
            class="history-item"
            :class="{ 
              active: activeConversationId === conversation.id,
              'assignment-help': conversation.title.includes('Assignment'),
              'study-tips': conversation.title.includes('Study')
            }"
            @click="loadConversation(conversation.id)"
          >
            <span class="conversation-icon">
              {{ conversation.title.includes('Assignment') ? '📝' : '📚' }}
            </span>
            {{ conversation.title.split(' - ')[0] }}
          </div>
        </div>
        
        <!-- Previous Chats -->
        <div v-if="previousConversations.length > 0" class="history-section">
          <h4 class="history-section-title">Previous Chats</h4>
          <div 
            v-for="conversation in previousConversations" 
            :key="conversation.id" 
            class="history-item"
            :class="{ 
              active: activeConversationId === conversation.id,
              'assignment-help': conversation.title.includes('Assignment'),
              'study-tips': conversation.title.includes('Study')
            }"
            @click="loadConversation(conversation.id)"
          >
            <span class="conversation-icon">
              {{ conversation.title.includes('Assignment') ? '📝' : '📚' }}
            </span>
            {{ conversation.title.split(' - ')[0] }}
          </div>
        </div>
        
        <div class="new-chat-btn" @click="showModeDialog = true">
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
              <div class="message-content" v-html="message.content"></div>
            </div>
          </div>
        </div>
        <div class="chat-input">
    <div class="input-container">
      <textarea
        ref="messageInput"
        v-model="userInput"
        placeholder="Type your message here..."
        @keydown="handleKeyDown"
        @input="adjustTextareaHeight"
        :disabled="!activeConversationId"
        rows="1"
      ></textarea>
      <div class="input-actions">
        <button class="send-btn" @click="sendMessage" :disabled="!activeConversationId">
          Send
        </button>
      </div>
    </div>
  </div>
      </div>
    </div>
    <div v-if="showModeDialog" class="mode-dialog-overlay">
      <div class="mode-dialog">
        <h3>Start New Chat</h3>
        <p>What type of assistance do you need?</p>
        <div class="mode-options">
          <button @click="createNewConversation('assignment_help')" class="mode-btn assignment-help">
            <span class="mode-icon">📝</span>
            <span class="mode-text">Assignment Help</span>
          </button>
          <button @click="createNewConversation('study_tips')" class="mode-btn study-tips">
            <span class="mode-icon">📚</span>
            <span class="mode-text">Study Tips</span>
          </button>
        </div>
        <button @click="showModeDialog = false" class="cancel-btn">Cancel</button>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted, nextTick, computed } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

import { marked } from 'marked';

const API_BASE_URL = "http://localhost:5000";
const router = useRouter();
const userInput = ref("");
const messageInput = ref(null);
const showModeDialog = ref(false);


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


const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

const adjustTextareaHeight = () => {
  nextTick(() => {
    const textarea = messageInput.value;
    if (textarea) {
      // Reset height to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set new height based on content
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  });
};

const todaysConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations.filter(conv => {
    // Add null check for created_at
    if (!conv.created_at) return false;
    
    try {
      const convDate = new Date(conv.created_at).toISOString().split('T')[0];
      return convDate === today;
    } catch (e) {
      console.error("Invalid date format:", conv.created_at);
      return false;
    }
  });
});

const renderMarkdown = (content) => {
  return marked.parse(content);
};

const previousConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations.filter(conv => {
    // Add null check for created_at
    if (!conv.created_at) return false;
    
    try {
      const convDate = new Date(conv.created_at).toISOString().split('T')[0];
      return convDate !== today;
    } catch (e) {
      console.error("Invalid date format:", conv.created_at);
      return false;
    }
  });
});

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
    
    // Add date validation
    const validatedConversations = response.data.map(conv => {
      if (!conv.created_at) {
        console.warn("Conversation missing created_at:", conv.id);
        conv.created_at = new Date().toISOString();
      }
      return conv;
    });
    
    conversations.splice(0, conversations.length, ...validatedConversations);
    
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
const startNewConversation = () => {
  showModeDialog.value = true;
};

const createNewConversation = async (mode) => {
  showModeDialog.value = false;
  try {
    loading.value = true;
    const token = localStorage.getItem("access_token");
    
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations`,
      { mode: mode },
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
    // Reset textarea height after sending
    if (messageInput.value) {
      messageInput.value.style.height = 'auto';
    }
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
};;

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
  
  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #1b408d;
  }
  .loading-state .spinner {
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top: 4px solid #1b408d;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin-right: 10px;
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  .chat-history::-webkit-scrollbar {
    width: 6px;
  }
  .chat-history::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .chat-history::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
  }
  .chat-history::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.5);
  }
  .chat-history::-webkit-scrollbar-thumb:active {
    background: rgba(255, 255, 255, 0.7);
  }
  .chat-history::-webkit-scrollbar-thumb:vertical {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
  }
  .chat-history::-webkit-scrollbar-thumb:vertical:hover {
    background: rgba(255, 255, 255, 0.5);
  }
  .chat-history::-webkit-scrollbar-thumb:vertical:active {
    background: rgba(255, 255, 255, 0.7);
  }
  .chat-history::-webkit-scrollbar-thumb:horizontal {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
  }
  .chat-history::-webkit-scrollbar-thumb:horizontal:hover {
    background: rgba(255, 255, 255, 0.5);
  }
  .chat-history::-webkit-scrollbar-thumb:horizontal:active {
    background: rgba(255, 255, 255, 0.7);
  }
  .chat-history::-webkit-scrollbar-corner {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .chat-history::-webkit-scrollbar-corner:active {
    background: rgba(255, 255, 255, 0.3);
  }
  .chat-history::-webkit-scrollbar-corner:hover {
    background: rgba(255, 255, 255, 0.5);
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
    max-height: fit-content;
  }
  
  input-container {
  display: flex;
  align-items: flex-end; /* Changed from center to flex-end */
  background-color: white;
  border-radius: 10px;
  padding: 10px 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.input-container textarea {
  flex: 1;
  border: none;
  resize: none;
  font-size: 14px;
  outline: none;
  max-height: 200px; /* Maximum height before scrolling */
  overflow-y: auto;
  padding: 8px 0;
  line-height: 1.5;
  font-family: inherit;
}

/* Remove the default textarea scrollbar when not needed */
.input-container textarea::-webkit-scrollbar {
  width: 6px;
}

.input-container textarea::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.input-container textarea::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

/* Adjust the send button position */
.input-actions {
  margin-left: 10px;
  margin-bottom: 5px;
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

.mode-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.mode-dialog {
  background-color: white;
  padding: 25px;
  border-radius: 10px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.mode-dialog h3 {
  margin-top: 0;
  color: #1b408d;
}

.mode-dialog p {
  margin-bottom: 20px;
  color: #555;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.mode-btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.assignment-help {
  background-color: #24b9f9;
  color: white;
}

.study-tips {
  background-color: #4CAF50;
  color: white;
}

.mode-icon {
  font-size: 1.2em;
}

.cancel-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 8px 15px;
  border-radius: 5px;
}

.cancel-btn:hover {
  background-color: #f0f0f0;
}

.history-section {
  margin-bottom: 15px;
}

.history-section-title {
  font-size: 0.9em;
  color: rgba(255, 255, 255, 0.7);
  margin: 10px 0 5px 0;
  padding-left: 10px;
}

.conversation-icon {
  margin-right: 8px;
}

/* Markdown formatted messages */
.message-content {
  white-space: pre-wrap;
  padding: 20px;
}

.message-content h1, 
.message-content h2, 
.message-content h3 {
  margin-top: 0.5em;
  margin-bottom: 0.3em;
}

.message-content p {
  margin-bottom: 0.8em;
  line-height: 1.2;
}

.message-content ul, 
.message-content ol {
  margin-bottom: 0.8em;
  padding-left: 1.5em;
}

.message-content li {
  margin-bottom: 0.3em;
}
  </style>