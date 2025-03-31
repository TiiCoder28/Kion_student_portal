import { defineStore } from 'pinia';
import api from '@/api/client'; // Use the configured axios instance
import { useRouter } from 'vue-router';

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    isLoading: false
  }),
  
  actions: {
    setUser(user) {
      this.userInfo = user;
    },

    async login(email, password) {
      try {
        this.isLoading = true;
        const response = await api.post(
          "/auth/login", 
          { email, password }
        );

        if (response.data.user) {
          this.setUser(response.data.user);
          return true;
        }
        return false;
      } catch (error) {
        console.error("Login failed:", error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async signup(userData) {
      try {
        this.isLoading = true;
        const response = await api.post(
          "/auth/signup",
          userData
        );

        if (response.data.user) {
          this.setUser(response.data.user);
          return true;
        }
        return false;
      } catch (error) {
        console.error("Signup failed:", error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchUser() {
      try {
        this.isLoading = true;
        const response = await api.get("/auth/user");
        
        if (response.data.user) {
          this.setUser(response.data.user);
        }
        return response.data.user;
      } catch (error) {
        if (error.response?.status === 401) {
          this.logout();
        }
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async checkAuth() {
      try {
        if (this.userInfo) return true;
        
        await this.fetchUser();
        return !!this.userInfo;
      } catch (error) {
        return false;
      }
    },

    async initialize() {
      try {
        await this.checkAuth();
      } catch (error) {
        console.error("Initialization error:", error);
      }
    },

    async logout() {
      try {
        await api.post("/auth/logout");
      } catch (error) {
        console.error("Logout error:", error);
      } finally {
        this.userInfo = null;
        const router = useRouter();
        router.push('/login');
      }
    }
  }
});