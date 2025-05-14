<template>
    <div class="archived-chats-container">
      <div class="header">
        <button class="back-btn" @click="router.go(-1)">
          ← Back
        </button>
        <h2>Archived Chats</h2>
      </div>
      
      <div class="content-container">
        <div class="archived-list">
          <div 
            v-for="conversation in archivedConversations" 
            :key="conversation.id" 
            class="archived-item"
            :class="{ 'active': selectedConversation?.id === conversation.id }"
            @click="loadConversation(conversation.id)"
          >
            <div class="conversation-info">
              <span class="conversation-icon">
                {{ getConversationIcon(conversation) }}
              </span>
              <div>
                <h3>{{ conversation.title }}</h3>
                <p class="last-active">
                  Last active: {{ formatDate(conversation.last_activity) }}
                </p>
              </div>
            </div>
            <button 
              class="delete-btn"
              @click.stop="deleteConversation(conversation.id)"
            >
              Delete
            </button>
          </div>
          
          <div v-if="archivedConversations.length === 0" class="empty-state">
            No archived conversations
          </div>
        </div>
        
        <!-- Conversation Viewer Panel -->
        <div v-if="selectedConversation" class="conversation-viewer">
          <div class="viewer-header">
            <h3>{{ selectedConversation.title }}</h3>
            <span class="archived-badge">Archived</span>
          </div>
          
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            Loading messages...
          </div>
          
          <div v-else class="messages-container">
            <div 
              v-for="(message, index) in messages" 
              :key="index" 
              class="message-container"
              :class="message.role"
            >
              <div class="message-avatar">
                <span v-if="message.role === 'assistant'">AI</span>
                <span v-else>{{ userInitials }}</span>
              </div>
              <div class="message-content">
                <div v-html="message.formattedContent"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  import { marked } from 'marked';
  import 'mathjax/es5/tex-mml-chtml';
  
  const API_BASE_URL = "http://localhost:5000";
  const router = useRouter();
  const archivedConversations = ref([]);
  const selectedConversation = ref(null);
  const messages = ref([]);
  const loading = ref(false);
  
  // User data (you might want to fetch this or get from store)
  const user = computed(() => ({
    firstName: localStorage.getItem('user_firstName') || '',
    lastName: localStorage.getItem('user_lastName') || ''
  }));
  
  const userInitials = computed(() => {
    return `${user.value.firstName?.charAt(0) || ''}${user.value.lastName?.charAt(0) || ''}`;
  });
  
  const fetchArchivedConversations = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.get(`${API_BASE_URL}/api/conversations/archived`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      archivedConversations.value = response.data;
    } catch (error) {
      console.error("Error fetching archived conversations:", error);
    }
  };
  
const loadConversation = async (conversationId) => {
  try {
    loading.value = true;
    messages.value = [];
    const token = localStorage.getItem("access_token");
    
    const response = await axios.get(
      `${API_BASE_URL}/api/conversations/${conversationId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    selectedConversation.value = response.data;
    
    // Filter out system messages and format each message
    const filteredMessages = response.data.messages.filter(msg => msg.role !== 'system');
    
    // Format each message's content
    for (const message of filteredMessages) {
      messages.value.push({
        ...message,
        formattedContent: await formatMessageContent(message.content)
      });
    }
    
  } catch (error) {
    console.error("Error loading conversation:", error);
  } finally {
    loading.value = false;
  }
};
  
  const formatMessageContent = async (content) => {
  try {
    // First process markdown
    let formatted = marked(content || '');
    
    // Then ensure MathJax is loaded and typeset if needed
    if (window.MathJax) {
      await window.MathJax.typesetPromise();
    }
    
    return formatted;
  } catch (e) {
    console.error("Formatting error:", e);
    return content;
  }
};
  
  const deleteConversation = async (conversationId) => {
    if (!confirm("Are you sure you want to permanently delete this conversation?")) return;
    
    try {
      const token = localStorage.getItem("access_token");
      await axios.delete(
        `${API_BASE_URL}/api/conversations/${conversationId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Remove from list
      archivedConversations.value = archivedConversations.value.filter(
        c => c.id !== conversationId
      );
      
      // Clear viewer if viewing deleted conversation
      if (selectedConversation.value?.id === conversationId) {
        selectedConversation.value = null;
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
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
  
  onMounted(() => {
    fetchArchivedConversations();

    if (typeof window.MathJax === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
      script.async = true;
      document.head.appendChild(script);
  }
  });
  </script>
  
  <style scoped>
  .archived-chats-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .header {
    display: flex;
    align-items: center;
    margin-bottom: 30px;
    position: relative;
  }
  
  .back-btn {
    background: none;
    border: none;
    font-size: 1.2em;
    cursor: pointer;
    margin-right: 15px;
  }
  
  .content-container {
    display: flex;
    gap: 20px;
  }
  
  .archived-list {
    flex: 1;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .archived-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .archived-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  }
  
  .archived-item.active {
    background-color: #f0f7ff;
    border-left: 4px solid #1b408d;
  }
  
  .conversation-info {
    display: flex;
    align-items: center;
    gap: 15px;
    flex: 1;
    min-width: 0;
  }
  
  .conversation-icon {
    font-size: 1.5em;
    flex-shrink: 0;
  }
  
  .conversation-info div {
    min-width: 0;
  }
  
  .conversation-info h3 {
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .last-active {
    font-size: 0.8em;
    color: #666;
    margin-top: 5px;
    white-space: nowrap;
  }
  
  .delete-btn {
    background: #ff6b6b;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    flex-shrink: 0;
  }
  
  .delete-btn:hover {
    background: #ff5252;
  }
  
  .empty-state {
    text-align: center;
    padding: 40px;
    color: #666;
    font-style: italic;
  }
  
  /* Conversation Viewer Styles */
  .conversation-viewer {
    flex: 2;
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
  }
  
  .viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
  }
  
  .archived-badge {
    background: #f0f0f0;
    color: #666;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
  }
  
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #666;
  }
  
  .spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top: 4px solid #1b408d;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin-bottom: 10px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
  }
  
  .message-container {
    display: flex;
    margin-bottom: 15px;
  }
  
  .message-container.user {
    justify-content: flex-end;
  }
  
  .message-container.assistant {
    justify-content: flex-start;
  }
  
  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: #1b408d;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    flex-shrink: 0;
  }
  
  .message-container.user .message-avatar {
    background-color: #24b9f9;
  }
  
.message-content {
  max-width: 80%;
  padding: 12px;
  border-radius: 8px;
  background-color: #f5f5f5;
  white-space: pre-wrap; /* Preserve line breaks */
  word-break: break-word; /* Prevent long words from overflowing */
}
  
.message-container.user .message-content {
    background-color: #e3f2fd;
}
  
.message-content >>> p {
  margin: 0.5em 0;
}

.message-content >>> h1,
.message-content >>> h2,
.message-content >>> h3,
.message-content >>> h4 {
  margin: 0.8em 0 0.5em 0;
}

.message-content >>> ul,
.message-content >>> ol {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.message-content >>> li {
  margin-bottom: 0.3em;
}

.message-content >>> code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

.message-content >>> pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.8em;
  border-radius: 4px;
  overflow-x: auto;
}

.message-content >>> blockquote {
  border-left: 3px solid #ccc;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #666;
}

.message-container.user .message-content {
  background-color: #e3f2fd;
}

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .content-container {
      flex-direction: column;
    }
    
    .archived-list {
      max-width: 100%;
    }
  }
  </style>