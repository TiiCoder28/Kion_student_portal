import { defineStore } from 'pinia';
import api from '@/api/client';

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [],
    currentConversation: null,
    isLoading: false
  }),

  actions: {
    async fetchConversations() {
        try {
          this.isLoading = true;
          const response = await api.get("/api/conversations");
  
          if (response.data) {
            this.conversations = response.data;
          }
          return response.data;
        } catch (error) {
          console.error("Conversations error:", error);
          if (error.response?.status === 401) {
            throw error; // Will be caught by the interceptor
          }
          throw error;
        } finally {
          this.isLoading = false;
        }
      },

    setCurrentConversation(conversation) {
      this.currentConversation = conversation;
    },

    async startNewChat() {
      this.currentConversation = null;
    },

    async sendMessage(message) {
      if (!message.trim()) return;

      try {
        this.isLoading = true;
        const response = await axios.post(
          "/api/chat",
          { message },
          { withCredentials: true,
            headers: {
                'Content-Type': 'application/json'
              }
           },
          
        );

        if (response.data) {
         
          if (!this.currentConversation) {
            this.conversations.unshift({
              id: response.data.conversation_id,
              title: response.data.title,
              chat_type: response.data.chat_type,
              created_at: new Date().toISOString()
            });
          }
          
         
          this.currentConversation = {
            id: response.data.conversation_id,
            title: response.data.title,
            chat_type: response.data.chat_type,
            messages: [
              { sender: 'user', content: message },
              { sender: 'ai', content: response.data.response }
            ]
          };
        }
      } catch (error) {
        console.error("Send message error:", error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async loadConversation(conversationId) {
      try {
        this.isLoading = true;
        const response = await axios.get(`/api/conversations/${conversationId}`, {
          withCredentials: true
        });

        if (response.data) {
          this.currentConversation = {
            ...response.data.conversation,
            messages: response.data.messages
          };
        }
      } catch (error) {
        console.error("Load conversation error:", error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async deleteConversation(conversationId) {
      try {
        await axios.delete(`/api/conversations/${conversationId}`, {
          withCredentials: true
        });
        
        this.conversations = this.conversations.filter(
          conv => conv.id !== conversationId
        );
        
        if (this.currentConversation?.id === conversationId) {
          this.currentConversation = null;
        }
      } catch (error) {
        console.error("Delete conversation error:", error);
        throw error;
      }
    }
  }
});