<template>
    <div class="archived-chats-container">
      <div class="header">
        <button class="back-btn" @click="router.go(-1)">
          ← Back
        </button>
        <h2>Archived Chats</h2>
      </div>
      
      <div class="archived-list">
        <div 
          v-for="conversation in archivedConversations" 
          :key="conversation.id" 
          class="archived-item"
          @click="restoreConversation(conversation.id)"
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
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  
  const API_BASE_URL = "http://localhost:5000";
  const router = useRouter();
  const archivedConversations = ref([]);
  
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
  
  const restoreConversation = async (conversationId) => {
    try {
      const token = localStorage.getItem("access_token");
      await axios.post(
        `${API_BASE_URL}/api/conversations/${conversationId}/restore`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // In a real app, you might want to navigate back to dashboard
      // and refresh the conversation list
      router.push('/dashboard');
    } catch (error) {
      console.error("Error restoring conversation:", error);
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
      
      archivedConversations.value = archivedConversations.value.filter(
        c => c.id !== conversationId
      );
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
  });
  </script>
  
  <style scoped>
  .archived-chats-container {
    max-width: 800px;
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
  
  .archived-list {
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
    transition: transform 0.2s;
  }
  
  .archived-item:hover {
    transform: translateY(-2px);
  }
  
  .conversation-info {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .conversation-icon {
    font-size: 1.5em;
  }
  
  .last-active {
    font-size: 0.8em;
    color: #666;
    margin-top: 5px;
  }
  
  .delete-btn {
    background: #ff6b6b;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
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
  </style>