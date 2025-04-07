<template>
  <div class="dashboard-container">
    <!-- Mobile Sidebar Toggle -->
    <div class="sidebar-toggle" @click="toggleSidebar">
      <span v-if="!sidebarOpen">☰</span>
      <span v-else>×</span>
    </div>

    <!-- Sidebar -->
    <div class="sidebar" :class="{ 'sidebar-open': sidebarOpen, 'sidebar-closed': !sidebarOpen }">
      <img src="../assets/images/kion-robot.png" alt="Kion Logo" class="logo" />
      <div class="user-info">
        <div class="user-avatar" @click="toggleUserMenu">
          <div class="avatar-initials">{{ userInitials }}</div>
          <div v-if="showUserMenu" class="user-menu">
            <button @click="logout">Logout</button>
          </div>
        </div>
        <h3 class="username">Welcome {{ user.firstName }} 👋!</h3>
      </div>

      <!-- New Chat Button at Top -->
      <div class="new-chat-btn" @click="showModeDialog = true">
        <span>+ New Chat</span>
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
            v-for="conversation in visiblePreviousConversations" 
            :key="conversation.id" 
            class="history-item"
            @click="loadConversation(conversation.id)"
          >
            <span class="conversation-icon">
              {{ conversation.title.includes('Assignment') ? '📝' : '📚' }}
            </span>
            {{ conversation.title.split(' - ')[0] }}
          </div>
          <div 
            v-if="previousConversations.length > visiblePreviousChats" 
            class="load-more-btn"
            @click="loadMoreChats"
          >
            Show More
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="main-content" :class="{ 'sidebar-collapsed': !sidebarOpen }">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading conversation...</p>
      </div>
      
      <div v-else class="chat-container">
        <div class="chat-messages">
          <div v-for="(message, index) in messages" :key="index" class="message-container">
            <div :class="['message', message.role === 'assistant' ? 'ai-message' : 'user-message']">
              <div class="avatar" :class="message.role">
                <span v-if="message.role === 'assistant'">AI</span>
                <span v-else>{{ userInitials }}</span>
              </div>
              <div class="message-content" v-html="message.content"></div>
            </div>
          </div>
          <div v-if="isTyping" class="message-container">
            <div class="message ai-message">
              <div class="avatar ai">AI</div>
              <div class="message-content">
                <div class="typing-loader">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Scroll to bottom button -->
        <button 
        v-if="showScrollButton" 
        class="scroll-to-bottom" 
        @click="scrollToBottom"
        aria-label="Scroll to bottom"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 5v14M19 12l-7 7-7-7"/>
        </svg>
      </button>
        
        <div class="chat-input">
          <div class="input-container">
            <textarea
              ref="messageInput"
              v-model="userInput"
              placeholder="Type your message here..."
              @keydown="handleKeyDown"
              @input="adjustTextareaHeight"
              :disabled="!activeConversationId || isTyping"
              rows="1"
            ></textarea>
            <div class="input-actions">
              <button class="send-btn" @click="sendMessage" :disabled="!activeConversationId || isTyping">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Chat Dialog -->
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
import { ref, reactive, onMounted, nextTick, computed, onBeforeUnmount } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { marked } from 'marked';

const API_BASE_URL = "http://localhost:5000";
const router = useRouter();
const userInput = ref("");
const messageInput = ref(null);
const showModeDialog = ref(false);
const sidebarOpen = ref(false);
const showScrollButton = ref(false);
const showWelcomeMessage = ref(false);


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
const isTyping = ref(false);
const visiblePreviousChats = ref(5);

const userInitials = computed(() => {
  return `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`;
});

const visiblePreviousConversations = computed(() => {
  return previousConversations.value.slice(0, visiblePreviousChats.value);
});

const loadMoreChats = () => {
  visiblePreviousChats.value += 5;
};

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
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  });
};

const todaysConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations
    .filter(conv => {
      if (!conv.created_at) return false;
      try {
        const convDate = new Date(conv.created_at).toISOString().split('T')[0];
        return convDate === today;
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));
});

const previousConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations
    .filter(conv => {
      if (!conv.created_at) return false;
      try {
        const convDate = new Date(conv.created_at).toISOString().split('T')[0];
        return convDate !== today;
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at));
});

// Toggle sidebar on mobile
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

// Check scroll position
const checkScrollPosition = () => {
  const chatContainer = document.querySelector('.chat-messages');
  if (chatContainer) {
    const { scrollTop, scrollHeight, clientHeight } = chatContainer;
    showScrollButton.value = scrollHeight - (scrollTop + clientHeight) > 100;
  }
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
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
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
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
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
  if (activeConversationId.value === conversationId) return;

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
  if (!userInput.value.trim() || !activeConversationId.value || isTyping.value) return;

  try {
    const token = localStorage.getItem("access_token");
    const messageContent = userInput.value;
    
    // Add user message
    messages.push({
      role: "user",
      content: messageContent,
      created_at: new Date().toISOString()
    });
    
    userInput.value = "";
    adjustTextareaHeight();
    await scrollToBottom();
    
    // Show loading indicator
    isTyping.value = true;
    
    // Send to backend
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations/${activeConversationId.value}/chat`,
      { message: messageContent },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    // Add AI response
    messages.push({
      role: "assistant",
      content: marked.parse(response.data.response),
      created_at: new Date().toISOString()
    });
    
    // Update conversation list
    await fetchConversations();
  } catch (error) {
    console.error("Error sending message:", error);
    messages.push({
      role: "assistant",
      content: "Sorry, I encountered an error processing your request.",
      created_at: new Date().toISOString()
    });
  } finally {
    isTyping.value = false;
    await scrollToBottom();
  }
};

// Helper function to scroll to bottom of chat
const scrollToBottom = async () => {
  await nextTick();
  const chatContainer = document.querySelector('.chat-messages');
  if (chatContainer) {
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: 'smooth'
    });
  }
  showScrollButton.value = false;
};

// Initialize component
onMounted(async () => {
  // Add scroll event listener
  const checkScrollPosition = () => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainer;
      showScrollButton.value = scrollHeight - (scrollTop + clientHeight) > 100;
    }
  };

  nextTick(() => {
    if(messageInput.value) {
      messageInput.value.focus();
    }
    
    const chatMessages = document.querySelector('.chat-messages');
    if (chatMessages) {
      chatMessages.addEventListener('scroll', checkScrollPosition);
    }
  });


  const logout = async () => {
  try {
    const token = localStorage.getItem("access_token");
    if (token) {
      await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    localStorage.removeItem("access_token");
    router.push("/login");
  } catch (error) {
    console.error("Logout failed:", error);
  }
};
  
  // Close sidebar if screen is larger than 768px
  const handleResize = () => {
    if (window.innerWidth > 768) {
      sidebarOpen.value = false;
    }
  };
  
  window.addEventListener('resize', handleResize);
  
  await fetchUserData();
  await fetchConversations();
});

const showUserMenu = ref(false);
const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value;
};

// Close user menu when clicking outside
const handleClickOutside = (event) => {
  const userAvatar = document.querySelector('.user-avatar');
  if (userAvatar && !userAvatar.contains(event.target)) {
    showUserMenu.value = false;
  }
};

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.dashboard-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #f9f9f9;
  position: relative;
}

.sidebar {
  width: 280px;
  background-color: #1b408d;
  color: white;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 10;
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
  margin-right: 10px;
  background-color: #24b9f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
}

.avatar.user {
  background-color: #24b9f9;
}

.avatar.ai {
  background-color: #1b408d;
}

.new-chat-btn {
  margin: 0 0 20px 0;
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
  font-weight: 500;
}

.new-chat-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

/* Custom scrollbar styling */
.chat-history::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-history::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.load-more-btn {
  padding: 8px;
  margin-top: 8px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.2s;
}

.load-more-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 5px;
  border-radius: 5px;
  cursor: pointer;
}

.history-item:hover, .history-item.active {
  background-color: rgba(255, 255, 255, 0.1);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  width: 100%;
  height: 100vh;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: linear-gradient(135deg, #0a1e4a, #1b408d);
  background-size: cover;
  position: relative;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 180px);
  scroll-behavior: smooth;
}

.message-container {
  margin-bottom: 10px;
  width: 100%;
  display: flex;
}

.ai-message {
  align-self: flex-start;
}

.user-message {
  align-self: flex-start;
  margin-left: auto;
}

.message {
  display: flex;
  align-items: flex-start;
  max-width: 80%;
}

.message-content {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  word-break: break-word;
}

.message .avatar {
  flex-shrink: 0;
  margin-right: 12px;
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

.input-container textarea {
  flex: 1;
  border: none;
  resize: none;
  font-size: 14px;
  outline: none;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px 0;
  line-height: 1.5;
  font-family: inherit;
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

.typing-loader {
  display: flex;
  gap: 5px;
  padding: 10px;
}

.typing-loader span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #1b408d;
  opacity: 0.4;
  animation: typingPulse 1.2s infinite ease-in-out;
}

.typing-loader span:nth-child(1) {
  animation-delay: 0s;
}

.typing-loader span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-loader span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingPulse {
  0%, 100% {
    opacity: 0.4;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-3px);
  }
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
  display: flex;
  flex-direction: column;
}

.history-section-title {
  font-size: 0.9em;
  color: rgba(255, 255, 255, 0.7);
  margin: 10px 0 5px 0;
  padding-left: 10px;
}

.conversation-icon {
  margin-right: 5px;
}

/* Scroll to bottom button */
.scroll-to-bottom {
  position: fixed;
  right: 30px;
  bottom: 100px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #24b9f9;
  color: white;
  border: none;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.2s;
}

.scroll-to-bottom:hover {
  background-color: #1da7e6;
  transform: scale(1.1);
}

/* Sidebar toggle button for mobile */
.sidebar-toggle {
  display: flex;
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 20;
  background-color: #1b408d;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.sidebar-closed {
  transform: translateX(-100%);
}

.sidebar-open {
  transform: translateX(0);
}

/* Main content adjustment when sidebar is closed */
.main-content {
  transition: margin-left 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: -280px;
}


.scroll-to-bottom {
  position: fixed;
  right: 30px;
  bottom: 100px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: #24b9f9;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.2s;
  opacity: 0.9;
}

.scroll-to-bottom:hover {
  background-color: #1da7e6;
  transform: scale(1.1);
  opacity: 1;
}

.scroll-to-bottom svg {
  width: 24px;
  height: 24px;
}

/* User menu styles */
.user-avatar {
  position: relative;
  cursor: pointer;
}

.user-menu {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 20;
  min-width: 120px;
  overflow: hidden;
}

.user-menu button {
  width: 100%;
  padding: 8px 16px;
  border: none;
  background: none;
  text-align: left;
  color: #333;
  cursor: pointer;
}

.user-menu button:hover {
  background-color: #f5f5f5;
}

/* Responsive styles */
@media (max-width: 768px) {

  .sidebar {
    width: 100%;
    height: auto;
    max-height: 60vh;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 100;
  }

  .chat-container {
    padding: 10px;
    height: calc(100vh - 120px); /* Adjust for mobile */
  }
  
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
  
  .main-content {
    margin-top: 60px; 
    height: calc(100vh - 60px);
  }
  
  
  .message {
    max-width: 90%;
  }
  
  .sidebar-toggle {
    display: flex;
  }
  
  .ai-message .message-content,
  .user-message .message-content {
    padding: 12px;
  }
  
  .scroll-to-bottom {
    right: 15px;
    bottom: 80px;
    width: 40px;
    height: 40px;
  }
  
.scroll-to-bottom svg {
  width: 20px;
  height: 20px;
}
}

/* Animation for sidebar */
.sidebar {
  transition: transform 0.3s ease;
}
</style>