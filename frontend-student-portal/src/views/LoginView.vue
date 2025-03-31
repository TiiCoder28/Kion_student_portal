<template>
    <div class="signup-container">
      <!-- Left Pane -->
      <div class="left-pane">
        <img src="../assets/images/kion-logo.png" alt="Kion Logo" class="logo" />
        <h1 class="title">Kion Consulting Student Assistant</h1>
        <img src="../assets/images/kion-robot.png" alt="Kion AI Assistant" class="robot-image" />
      </div>
  
      <!-- Right Pane (Login Form) -->
      <div class="right-pane">
        <div class="form-container">
          <h2 class="form-title">Welcome Back</h2>
          <p class="form-subtitle">Login to access your account</p>
  
          <form @submit.prevent="handleLogin">
            <input type="email" placeholder="Email Address" v-model="email" required />
            <input type="password" placeholder="Password" v-model="password" required />
            
            <button type="submit" class="signup-btn">Login</button>
          </form>
          
          <p class="login-text">
            Don't have an account? <router-link to="/signup" class="login-link">Sign Up</router-link>
          </p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from "vue";
  import axios from "axios";
  import { useRouter } from "vue-router";
  
  const email = ref("");
  const password = ref("");
  const router = useRouter();
  
  const handleLogin = async () => {
    try {
      const response = await axios.post("http://localhost:5000/auth/login", {
        email: email.value,
        password: password.value,
      });
  
      if (response.status === 200) {
        // Save the JWT token and user details to localStorage
        const { access_token, user } = response.data;
        localStorage.setItem("access_token", response.data.access_token);
        localStorage.setItem("user", JSON.stringify(user));  // Save user details
  
        // Redirect to the dashboard
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Login error:", error.response?.data || error.message);
      alert(error.response?.data?.error || "Login failed. Please try again.");
    }
  };
  </script>
  
  <style scoped>
  .signup-container {
    display: flex;
    height: 100vh;
  }
  
  .left-pane {
    width: 40%;
    background-color: #1b408d;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 20px;
    position: relative;
  }
  
  .robot-image {
    width: 300px;
    height: auto;
    margin-top: 20px;
  }
  
  .title {
    font-size: 3rem;
    font-weight: bold;
    color: white;
    margin-bottom: 2rem;
    position: relative;
    z-index: 1;
  }
  
  .logo {
    width: 120px;
    height: auto;
    position: absolute;
    top: 20px;
    left: 20px;
  }
  
  .right-pane {
    width: 60%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f9f9f9;
  }
  
  .form-container {
    width: 350px;
    text-align: center;
  }
  
  .form-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
  }
  
  .form-subtitle {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 20px;
  }
  
  input {
    width: 100%;
    padding: 10px;
    margin: 8px 0;
    border: 1px solid #ccc;
    border-radius: 5px;
  }
  
  .signup-btn {
    width: 100%;
    background-color: #1b408d;
    color: white;
    padding: 10px;
    font-size: 16px;
    font-weight: bold;
    border: none;
    border-radius: 5px;
    transition: 0.3s;
  }
  
  .signup-btn:hover {
    background-color: #163b7a;
  }
  
  .login-text {
    margin-top: 15px;
    font-size: 14px;
  }
  
  .login-link {
    color: #1b408d;
    text-decoration: none;
  }
  </style>
  