<template>
  <div class="background-container">
    <div class="overlay"></div>

    <!-- Logo -->
    <img src="../assets/images/kion-logo.png" alt="Kion Consulting Logo" style="" />

    <h1 class="heading">Kion Consulting Student Assistant</h1>
    <p class="description">Welcome to your personal AI-powered assistant. Sign up or log in to get started!</p>
    
    <div class="button-container">
      <button @click="goToSignup" class="action-button">Sign Up</button>
      <button @click="goToLogin" class="action-button">Log In</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goToSignup = () => {
  router.push('/signup');
};

const goToLogin = () => {
  router.push('/login');
};

</script>

<style scoped>
.background-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  text-align: center;
  background: url('../assets/images/background-image.jpg') no-repeat center center/cover;
  position: relative;
  overflow: hidden;
}

.logo {
  width: 100px; 
  margin-bottom: 2rem; 
  position: relative; 
  z-index: 1;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(9, 41, 52, 0.4);
}

.heading {
  font-size: 2rem;
  font-weight: bold;
  color: white;
  margin-bottom: 1rem;
  position: relative;
  z-index: 1;
}

.description {
  font-size: 1.2rem;
  color: white;
  max-width: 600px;
  margin-bottom: 1.5rem;
  position: relative;
  z-index: 1;
}

.button-container {
  display: flex;
  gap: 1rem;
  position: relative;
  z-index: 1;
}

.action-button {
  background-color: #1b408d;
  color: white;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: bold;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s ease-in-out;
}

.action-button:hover {
  transform: scale(1.05);
}

link {
  text-decoration: none;
}
</style>
