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
        <h3 class="username">Welcome {{ user.firstName }} 👋!</h3>
      </div>

      <!-- New Chat Button at Top -->
      <div class="new-chat-btn" @click="showModeDialog = true">
        <span>+ New Chat</span>
      </div>

      <div class="chat-history">
        <h3>Chat History</h3>
        
        <!-- No chats message -->
        <div v-if="todaysConversations.length === 0 && previousConversations.length === 0" class="no-chats-message">
          No previous chats
        </div>

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
              {{ getConversationIcon(conversation) }}
            </span>
            {{ conversation.title }}
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
              {{ getConversationIcon(conversation) }}
            </span>
            {{ conversation.title }}
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

        <h2 class="chat-title">
          <div class="user-info">
          <div class="header-avatar" @click="toggleUserMenu">
            <div class="avatar-initials">{{ userInitials }}</div>
            <div v-if="showUserMenu" class="user-menu">
              <button @click="navigateToArchived">Archived Chats</button>
              <button @click="handleLogout">Logout</button>
            </div>
          </div>
          </div>
          {{ activeConversationId ? conversations.find(c => c.id === activeConversationId)?.title : 'Create a conversation' }}
          <div class="chat-header-actions" v-if="activeConversationId">
          <button class="btn btn-primary" @click="confirmClearChat">
            Clear Chat
          </button>
        </div>
        </h2>
        
        <div v-if="showWelcomeMessage" class="welcome-message">
          <h3>Welcome, {{ user.firstName }}! 👋. My name is Thuto</h3>
          <p>Get started by choosing a conversation from the sidebar or starting a new chat with one of our tutors</p>
          <div class="welcome-illustration">
            <div class="robot-icon">🤖</div>
            <p class="tip-text">
              Pro tip: You can say things like<br>
              <span v-for="(tip, index) in getModeSpecificTips()" :key="index">
                "{{ tip }}"<br v-if="index < getModeSpecificTips().length - 1">
              </span>
            </p>
            <button 
              v-if="!activeConversationId" 
              class="start-chat-btn"
              @click="showModeDialog = true"
            >
              Start Chat
            </button>
          </div>
        </div>
        <div class="chat-messages">
          <div v-for="(message, index) in messages.filter(m => m.role !== 'system')" 
            :key="index" 
            class="message-container">
            <div :class="['message', message.role === 'assistant' ? 'ai-message' : 'user-message']">
              <div class="avatar" :class="message.role">
                <span v-if="message.role === 'assistant'">AI</span>
                <span v-else>{{ userInitials }}</span>
              </div>
              <div class="message-content" v-html="message.formattedContent"></div>
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
            @click="scrollToBottom()"
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
      <button @click="selectMode('tutor')" class="mode-btn tutor-mode">
        <span class="mode-icon">👨‍🏫</span>
        <span class="mode-text">Tutor</span>
      </button>
      <button @click="selectMode('study_tips')" class="mode-btn study-tips">
        <span class="mode-icon">📚</span>
        <span class="mode-text">Study Tips</span>
      </button>
    </div>
    
    <!-- Tutor Sub-Mode Selection (shown only when tutor is selected) -->
    <div v-if="selectedMode === 'tutor'" class="sub-mode-options">
          <h4>Select Subject:</h4>
          <button @click="createNewConversation('tutor', 'math')" class="sub-mode-btn math-tutor">
            <span class="sub-mode-icon">🧮</span>
            <span class="sub-mode-text">Mathematics</span>
          </button>
          <button @click="createNewConversation('tutor', 'english')" class="sub-mode-btn english-tutor">
            <span class="sub-mode-icon">📖</span>
            <span class="sub-mode-text">English</span>
          </button>
          <button @click="createNewConversation('tutor', 'history')" class="sub-mode-btn history-tutor">
            <span class="sub-mode-icon">🏛️</span>
            <span class="sub-mode-text">History</span>
          </button>
          <button @click="createNewConversation('tutor', 'geography')" class="sub-mode-btn geography-tutor">
            <span class="sub-mode-icon">🗺️</span>
            <span class="sub-mode-text">Geography</span>
          </button>
          <button @click="createNewConversation('tutor', 'physical_science')" class="sub-mode-btn science-tutor">
            <span class="sub-mode-icon">⚛️</span>
            <span class="sub-mode-text">Physical Science</span>
          </button>
          <button @click="createNewConversation('tutor', 'general')" class="sub-mode-btn general-tutor">
            <span class="sub-mode-icon">🌟</span>
            <span class="sub-mode-text">General Tutor</span>
          </button>
        </div>
        
        <button @click="showModeDialog = false" class="cancel-btn">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed, onBeforeUnmount, watch } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";
import { marked } from 'marked';
import 'mathjax/es5/tex-mml-chtml';


const API_BASE_URL = "http://localhost:5000";
const router = useRouter();
const userInput = ref("");
const messageInput = ref(null);
const showModeDialog = ref(false);
const sidebarOpen = ref(false);
const showScrollButton = ref(false);
const selectedMode = ref(null);

const navigateToArchived = () => {
  router.push('/archived-chats');
};

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
const showUserMenu = ref(false);



const userInitials = computed(() => {
  return `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`;
});

const visiblePreviousConversations = computed(() => {
  return previousConversations.value.slice(0, visiblePreviousChats.value);
});

const loadMoreChats = () => {
  visiblePreviousChats.value += 5;
};

const showWelcomeMessage = computed(() => {
  return messages.length === 0 || !activeConversationId.value;
});

const confirmClearChat = () => {
  if (confirm("Are you sure you want to clear this chat? The conversation will be archived and a new one will be created.")) {
    clearAndRestartChat();
  }
};

const clearAndRestartChat = async () => {
  try {
    const token = localStorage.getItem("access_token");
    const currentConv = conversations.find(c => c.id === activeConversationId.value);
    
    if (!currentConv) return;
    
    // Archive the current conversation
    await axios.post(
      `${API_BASE_URL}/api/conversations/${activeConversationId.value}/archive`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    // Create a new conversation with same mode/sub_mode
    const payload = {
      mode: currentConv.mode
    };
    
    if (currentConv.sub_mode) {
      payload.sub_mode = currentConv.sub_mode;
    }
    
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations`,
      payload,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    // Update local state
    const index = conversations.findIndex(c => c.id === activeConversationId.value);
    if (index > -1) {
      conversations[index].is_active = false;
    }
    
    conversations.unshift(response.data);
    await loadConversation(response.data.id);
    
  } catch (error) {
    console.error("Error clearing chat:", error);
  }
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

const currentConversationMode = computed(() => {
  if (!activeConversationId.value) return null;
  const conv = conversations.find(c => c.id === activeConversationId.value);
  return conv ? { mode: conv.mode, sub_mode: conv.sub_mode } : null;
});

const getModeSpecificTips = () => {
  if (!currentConversationMode.value) {
    return [
      "Help me with algebra basics",
      "Create a study schedule for exams",
      "Explain photosynthesis to me"
    ];
  }

  const { mode, sub_mode } = currentConversationMode.value;
  
  if (mode === 'tutor') {
    switch(sub_mode) {
      case 'math':
        return [
          "Help me solve this quadratic equation: x² + 5x + 6 = 0",
          "What is the Pythagorean theorem?",
          "Explain derivatives in calculus"
        ];
      case 'english':
        return [
          "Name the different parts of speech",
          "Help me analyze this poem",
          "What's the difference between active and passive voice?"
        ];
      case 'general':
        return [
          "Explain the scientific method",
          "Help me understand World War II causes",
          "What are Newton's laws of motion?"
        ];
      case 'history':
        return [
          "Tell me about the French Revolution",
          "What were the causes of the Cold War?",
          "Explain the significance of the Magna Carta"
        ];
      case 'geography':
        return [
          "What are the major rivers in Africa?",
          "Explain the concept of plate tectonics",
          "Describe the climate zones of the world"
        ];
      case 'physical_science':
        return [
          "Explain the laws of thermodynamics",
          "What is the difference between speed and velocity?",
          "Describe the structure of an atom"
        ];
      default:
        return [
          "Help me with algebra basics",
          "Create a study schedule for exams"
        ];
    }
  } else if (mode === 'study_tips') {
    return [
      "How can I improve my focus while studying?",
      "What's the Pomodoro technique?",
      "Best ways to prepare for final exams"
    ];
  }
  
  return [
    "Help me with algebra basics",
    "Create a study schedule for exams"
  ];
};

const todaysConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations
    .filter(conv => {
      if (!conv.last_activity) return false;
      try {
        const convDate = new Date(conv.last_activity).toISOString().split('T')[0];
        return convDate === today;
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => new Date(b.last_activity) - new Date(a.last_activity));
});

const previousConversations = computed(() => {
  const today = new Date().toISOString().split('T')[0];
  return conversations
    .filter(conv => {
      if (!conv.last_activity) return false;
      try {
        const convDate = new Date(conv.last_activity).toISOString().split('T')[0];
        return convDate !== today;
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => new Date(b.last_activity) - new Date(a.last_activity));
});

const selectMode = (mode) => {
  if (mode === 'tutor') {
    selectedMode.value = 'tutor';
  } else {
    createNewConversation(mode);
  }
};

const getConversationIcon = (conversation) => {
  if (!conversation) return '📚';
  if (conversation.mode === 'study_tips') return '📚';
  if (conversation.sub_mode === 'math') return '🧮';
  if (conversation.sub_mode === 'english') return '📖';
  if (conversation.sub_mode === 'history') return '🏛️';
  if (conversation.sub_mode === 'geography') return '🗺️';
  if (conversation.sub_mode === 'physical_science') return '⚛️';
  return '🌟';
};

const configureMathJax = () => {
  window.MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      processEscapes: true,
      packages: {'[+]': ['ams', 'physics', 'siunitx']}, // Added physics and siunitx
      macros: {
        degC: '^{\\circ}\\mathrm{C}', // Shortcut for degrees Celsius
        kelvin: '\\mathrm{K}',
        celsius: '^{\\circ}\\mathrm{C}'
      }
    },
    loader: {load: ['[tex]/physics', '[tex]/siunitx']}, // Load additional packages
    startup: {
      typeset: false
    }
  };
};

// Toggle sidebar on mobile
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value;
};

const loadMathJax = () => {
  return new Promise((resolve) => {
    if (window.MathJax) {
      resolve(); // Already loaded
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    script.async = true;
    script.onload = resolve;
    document.head.appendChild(script);
  });
};

const formatMessageContent = async (content) => {
  try {
    // First process with marked for markdown
    let processed = marked(content || '');

    if (window.MathJax) {
      await window.MathJax.typesetPromise();
    }

    return processed;
  } catch (e) {
    console.error("Formatting error:", e);
    return content; 
  }
};


// const renderMathInMessage = async (content) => {
//   // Process display math ($$...$$)
//   let processed = content.replace(/\$\$(.*?)\$\$/gs, (_, formula) => {
//     try {
//       return katex.renderToString(formula, {
//         throwOnError: false,
//         displayMode: true
//       });
//     } catch (err) {
//       console.error("Error rendering math:", err);
//       return `<div class="math-error">$${formula}$</div>`;
//     }
//   });
  
//   // Process inline math ($...$)
//   processed = processed.replace(/\$(.*?)\$/g, (_, formula) => {
//     try {
//       return katex.renderToString(formula, {
//         throwOnError: false,
//         displayMode: false
//       });
//     } catch (err) {
//       console.error("Error rendering inline math:", err);
//       return `<span class="math-error">$${formula}$</span>`;
//     }
//   });
  
//   return processed;
// };

const checkScrollPosition = () => {
  const chatContainer = document.querySelector('.chat-messages');
  if (chatContainer) {
    // Calculate if user has scrolled up (with 100px threshold)
    const threshold = 100;
    const fromBottom = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight;
    console.log(`Distance from bottom: ${fromBottom}px`);
    showScrollButton.value = fromBottom > threshold;
    console.log(`Show scroll button: ${showScrollButton.value}`);
  }
};

const scrollToBottom = async (behavior = 'smooth') => {
  await nextTick();
  const chatContainer = document.querySelector('.chat-messages');
  if (chatContainer) {
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: behavior
    });
    showScrollButton.value = false;
  }
};

// Fetch user data
const fetchUserData = async () => {
  try {
    const token = localStorage.getItem("access_token");
    console.log("Raw token:", token); // Verify token exists
    
    const response = await axios.get(`${API_BASE_URL}/auth/user`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.data) {
      user.firstName = response.data.first_name;
      user.lastName = response.data.last_name;
      user.email = response.data.email;
    }
  } catch (error) {
    console.error("Detailed auth error:", {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
      config: error.config
    });
    
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      router.push("/login");
    }
  }
};



// Fetch all conversations for the user
const fetchConversations = async () => {
  try {
    loading.value = true;
    const token = localStorage.getItem("access_token")

    console.log(token)
    const response = await axios.get(`${API_BASE_URL}/api/conversations`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }, withCredentials: true
    });
    
    // Ensure all conversations have last_activity
    const validatedConversations = response.data.map(conv => {
      if (!conv.last_activity) {
        console.warn("Conversation missing last_activity:", conv.id);
        conv.last_activity = conv.created_at || new Date().toISOString();
      }
      return conv;
    });
    
    conversations.splice(0, conversations.length, ...validatedConversations);
    
    if (conversations.length > 0) {
      await loadConversation(conversations[0].id);
    } else {
      // No conversations exist - ensure welcome message shows
      activeConversationId.value = null;
      messages.splice(0, messages.length);
    }

  } catch (error) {
    console.error("Error fetching conversations:", error);
    if (error.response && error.response.status === 401) {
    }
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
        Authorization: `Bearer ${token}`,
      }
    });
    
    messages.splice(0, messages.length);

    if (response.data.messages && response.data.messages.length > 0) {
      for (const msg of response.data.messages) {
        if (msg.role === 'system') continue; // Skip system messages
        
        const formattedContent = await formatMessageContent(msg.content);
        messages.push({
          ...msg,
          formattedContent: formattedContent
        });
      }
    }
    
    scrollToBottom();
  } catch (error) {
    console.error("Error loading conversation:", error);
  } finally {
    loading.value = false;
  }
}

// Create a new conversation
const createNewConversation = async (mode, subMode = null) => {
  showModeDialog.value = false;
  selectedMode.value = null;
  
  try {
    loading.value = true;
    const token = localStorage.getItem("access_token");
    
    const payload = {
      mode: mode
    };
    
    if (mode === 'tutor' && subMode) {
      payload.sub_mode = subMode;
    }
    
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations`,
      payload,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
    );
    
    conversations.unshift(response.data);
    activeConversationId.value = response.data;
    await loadConversation(response.data.id);

    messages.splice(0, messages.length);

    let welcomeMessage = "";
    if (mode === 'tutor') {
      welcomeMessage = {
        math: `Hi ${user.firstName}! 👋 I'm your Mathematics tutor. What concepts would you like help with today?`,
        english: `Hello ${user.firstName}! 📚 I'm your English tutor. How can I assist you today?`,
        history: `Greetings ${user.firstName}! 🏛️ I'm your History tutor. What historical events are you curious about?`,
        geography: `Hi ${user.firstName}! 🗺️ I'm your Geography tutor. What geographical topics would you like to explore?`,
        physical_science: `Hello ${user.firstName}! ⚛️ I'm your Physical Science tutor. What scientific concepts would you like to learn about?`,
        general: `Hi there ${user.firstName}! 🌟 I'm your general tutor. What would you like to learn about?`
      }[subMode];
    } else {
      welcomeMessage = `Hey ${user.firstName}! 🚀 Let's build some awesome study habits! Where should we start?`;
    }
    
    // Format the welcome message properly
    const formattedWelcome = await formatMessageContent(welcomeMessage);
    
    messages.push({
      role: "assistant",
      content: welcomeMessage,
      formattedContent: formattedWelcome,
      created_at: new Date().toISOString()
    });
    
    nextTick(() => {
      if (messageInput.value) {
        messageInput.value.focus();
      }
      scrollToBottom();
    });
  } catch (error) {
    console.error("Error creating conversation:", {
      error: error.response?.data || error.message,
      status: error.response?.status
    });
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
    const userMsg = {
      role: "user",
      content: messageContent,
      formattedContent: await formatMessageContent(messageContent),
      created_at: new Date().toISOString()
    };
    messages.push(userMsg);
    
    userInput.value = "";
    adjustTextareaHeight();
    await scrollToBottom();
    
    isTyping.value = true;
    
    const response = await axios.post(
      `${API_BASE_URL}/api/conversations/${activeConversationId.value}/chat`,
      { message: messageContent },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    const aiMsg = {
      role: "assistant",
      content: response.data.response,
      formattedContent: await formatMessageContent(response.data.response),
      created_at: new Date().toISOString()
    };
    messages.push(aiMsg);
    
    
    const now = new Date().toISOString();
    const convIndex = conversations.findIndex(c => c.id === activeConversationId.value);
    if (convIndex > -1) {
      conversations[convIndex].last_activity = now;
      
      // Move to top if not already there
      if (convIndex > 0) {
        const [activeConv] = conversations.splice(convIndex, 1);
        conversations.unshift(activeConv);
      }
    }
    
  } catch (error) {
    console.error("Error sending message:", error);
    messages.push({
      role: "assistant",
      content: "Sorry, I encountered an error processing your request.",
      formattedContent: "Sorry, I encountered an error processing your request.",
      created_at: new Date().toISOString()
    });
  } finally {
    isTyping.value = false;
    await scrollToBottom();
  }
};


const logout = async () => {
  try {
    const token = localStorage.getItem("access_token");
    if (token) {
      await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        withCredentials: true
      });
    }
    localStorage.removeItem("access_token");
    router.push("/login");
  } catch (error) {
    console.error("Logout failed:", error);
    localStorage.removeItem("access_token");
    router.push("/login");
  }
};
  

watch(() => messages, async (newVal) => {
  await nextTick();
  if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
    try {
      console.log('Typesetting math...');
      await window.MathJax.typesetPromise();
      console.log('Math typeset complete');
    } catch (e) {
      console.error('MathJax error:', e);
    }
  }
}, { deep: true, immediate: true });

// Initialize component
onMounted(async () => {

  await loadMathJax();

  const token = localStorage.getItem("access_token");
  if (!token) {
    router.push("/login");
    return;
  }

  await fetchUserData();
  await fetchConversations();

  nextTick(() => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      chatContainer.addEventListener('scroll', checkScrollPosition);
    }
    scrollToBottom('auto');
    
    if (window.MathJax) {
      window.MathJax.typesetPromise();
    }
  });


  const handleResize = () => {
    if (window.innerWidth > 768) {
      sidebarOpen.value = false;
    }
  };
  
  window.addEventListener('resize', handleResize);

  checkScrollPosition();
});


const toggleUserMenu = (e) => {
  e.stopPropagation();
  showUserMenu.value = !showUserMenu.value;
};

const handleLogout = (e) => {
  e.stopPropagation();
  logout();
};


const handleClickOutside = (event) => {
  const userAvatar = document.querySelector('.user-avatar');
  if (userAvatar && !userAvatar.contains(event.target)) {
    showUserMenu.value = false;
  }
};

onBeforeUnmount(() => {
  const chatContainer = document.querySelector('.chat-messages');
  if (chatContainer) {
    chatContainer.removeEventListener('scroll', checkScrollPosition);
  }
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
  z-index: 100;
}

.logo {
  width: 100px;
  height: auto;
  margin-bottom: 30px;
}

.user-info {
  display: flex;
  padding: 10px;
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
  position: relative;
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

.chat-title {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  color: white;
  text-align: center;
  padding: 1rem 0;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.chat-header-actions {
  position: absolute;
  left: 20px;
  top: 20px;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: #24b9f9;
  color: white;
}

.btn-primary:hover {
  background-color: #1da7e6;
}


.clear-chat-btn {
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 5px 15px;
  font-size: 0.8em;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-chat-btn:hover {
  background: #e9ecef;
}

.header-avatar {
  position: absolute;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #24b9f9;
  display: flex;
  padding: 10px;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  cursor: pointer;
}

.welcome-message {
  text-align: center;
  padding: 2rem;
  color: white;
  animation: fadeIn 0.5s ease-in;
}

.welcome-message h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #24b9f9;
}

.welcome-message p {
  font-size: 1rem;
  opacity: 0.8;
  line-height: 1.5;
}

.welcome-illustration {
  margin-top: 2rem;
  text-align: center;
}

.start-chat-btn {
  background-color: #24b9f9;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  margin-top: 20px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.start-chat-btn:hover {
  background-color: #1da7e6;
  transform: translateY(-2px);
}

.robot-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: bounce 2s infinite;
}

.tip-text {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.4;
  max-width: 400px;
  margin: 0 auto;
}
.tip-text span {
  display: inline-block;
  margin: 0.2rem 0;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tutor-mode {
  background-color: #6c5ce7;
  color: white;
}

.sub-mode-options {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.sub-mode-btn {
  padding: 10px;
  margin: 5px 0;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  text-align: left;
}

.math-tutor {
  background-color: #00b894;
  color: white;
}

.english-tutor {
  background-color: #0984e3;
  color: white;
}

.general-tutor {
  background-color: #6c5ce7;
  color: white;
}

.history-tutor {
  background-color: #8e44ad;
  color: white;
}

.geography-tutor {
  background-color: #27ae60;
  color: white;
}

.science-tutor {
  background-color: #3498db;
  color: white;
}
.sub-mode-icon {
  font-size: 1.2em;
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

.katex {
  font-size: 1.1em !important;
}

.katex-display {
  margin: 0.5em 0;
  padding: 0.5em;
  overflow-x: auto;
  overflow-y: hidden;
}

.math-error {
  color: #e74c3c;
  background-color: #fde8e8;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.message-content {
  white-space: pre-wrap;
  padding: 20px;
}

.message-content :is(strong, b) {
  font-weight: bold;
}

.message-content :is(em, i) {
  font-style: italic;
}

.message-content h1, 
.message-content h2, 
.message-content h3, 
.message-content h4 {
  margin: 0.5em 0;
  font-weight: bold;
}

.message-content h1 {
  font-size: 1.5em;
}

.message-content h2 {
  font-size: 1.3em;
}

.message-content h3 {
  font-size: 1.1em;
}


.message-content p {
  margin-bottom: 0.8em;
  line-height: 1.2;
  font-size: 0.8em;
}

.message-content ul, 
.message-content ol {
  margin-bottom: 0.8em;
  padding-left: 1.5em;
}

.message-content li {
  margin-bottom: 0.3em;
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

.no-chats-message {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.3rem;
  text-align: center;
  padding: 20px;
  font-style: italic;
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
  z-index: 1000;
  transition: all 0.2s;
  opacity: 0.9;
}

.scroll-to-bottom:hover {
  background-color: #1da7e6;
  transform: scale(1.1);
  opacity: 1;
}

.scroll-to-bottom svg {
  width: 20px;
  height: 20px;
}

.scroll-to-bottom svg {
  width: 20px;
  height: 20px;
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
  right: 0;
  transform: none;
  background-color: white;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-width: 180px;
  overflow: hidden;
}

.user-menu button {
  display: block;
  width: 100%;
  padding: 10px 15px;
  border: none;
  background: none;
  text-align: left;
  color: #333;
  cursor: pointer;
}

.user-menu button:hover {
  background-color: #f5f5f5;
}

.MathJax {
  font-size: 1.1em;
  color: inherit !important;
}

.ai-message .MathJax {
  color: #333 !important;
}

.user-message .MathJax {
  color: white !important;
}

.MathJax_Display {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.5em 0;
}

.math-error {
  color: #e74c3c;
  background-color: #fde8e8;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

/* Responsive styles */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
  
  .main-content {
    margin-left: 0;
    width: 100%;
  }
  
  .sidebar-toggle {
    display: flex;
  }


.chat-container {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
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