<template>
    <div class="signup-container">
      <!-- Left Pane -->
      <div class="left-pane">
        <img src="../assets/images/kion-logo.png" alt="Kion Logo" class="logo" />
        <h1 class="heading">Kion Consulting Student Assistant</h1>
        <img src="../assets/images/kion-robot.png" alt="Kion AI Assistant" class="robot-image" />
      </div>
  
      <!-- Right Pane (Signup Form) -->
      <div class="right-pane">
        <div class="form-container">
          <h2 class="form-title">Create Your Account</h2>
          <p class="form-subtitle">Enter your details to get started</p>
  
          <form @submit.prevent="handleSignup">
            <div class="input-group">
              <input type="text" placeholder="First Name" v-model="firstName" required />
              <input type="text" placeholder="Last Name" v-model="lastName" required />
            </div>
  
            <input type="email" placeholder="Email Address" v-model="email" required />
            <input type="email" placeholder="Confirm Email Address" v-model="confirmEmail" required />
            <input type="password" placeholder="Password" v-model="password" required />
            <input type="password" placeholder="Confirm Password" v-model="confirmPassword" required />
  
            <button type="submit" class="signup-btn">Sign Up</button>
          </form>
  
          <p class="login-text">
            Already have an account? <a href="/login" class="login-link">Login</a>
          </p>
        </div>
      </div>
    </div>
  </template>
  
 <script setup>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

const firstName = ref("");
const lastName = ref("");
const email = ref("");
const confirmEmail = ref("");
const password = ref("");
const confirmPassword = ref("");
const router = useRouter();

const handleSignup = async () => {
  // Basic validation
  if (email.value !== confirmEmail.value) {
    alert("Emails do not match!");
    return;
  }
  if (password.value !== confirmPassword.value) {
    alert("Passwords do not match!");
    return;
  }

  try {
    const response = await axios.post("http://localhost:5000/auth/signup", {
      first_name: firstName.value,
      last_name: lastName.value,
      email: email.value,
      password: password.value,
    });

    if (response.status === 201) {
      // Save the JWT token and user details to localStorage
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("user", JSON.stringify(user));  // Save user details

      // Redirect to the dashboard
      router.push("/dashboard");
    }
  } catch (error) {
    console.error("Signup error:", error.response?.data || error.message);
    alert(error.response?.data?.error || "Signup failed. Please try again.");
  }
};
</script>
  
  <style scoped>
  /* Main container */
  .signup-container {
    display: flex;
    height: 100vh;
  }
  
  /* Left Pane */
  .left-pane {
  width: 40%;
  background-color: #1b408d;
  display: flex;
  flex-direction: column;
  align-items: center; /* Keep content centered */
  justify-content: center;
  text-align: center;
  padding: 20px;
  position: relative;
}

.robot-image {
  width: 300px; /* Adjust size as needed */
  height: auto;
  margin-top: 20px; /* Space between heading and robot image */
}

  .heading {
  font-size: 3rem;
  font-weight: bold;
  color: white;
  margin-bottom: 2rem;
  position: relative;
  z-index: 1;
}

  /* Logo */
  .logo {
  width: 120px; /* Make the logo smaller */
  height: auto;
  position: absolute;
  top: 20px; /* Move to the top */
  left: 20px; /* Move to the left */
}
  
  /* Right Pane */
  .right-pane {
    width: 60%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f9f9f9;
  }
  
  /* Form Container */
  .form-container {
    width: 350px;
    text-align: center;
  }
  
  /* Titles */
  .form-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
  }
  
  .form-subtitle {
    font-size: 14px;
    color: #666;
    margin-bottom: 20px;
  }
  
  /* Input Fields */
  .input-group {
    display: flex;
    gap: 10px;
  }
  
  input, select {
    width: 100%;
    padding: 10px;
    margin: 8px 0;
    border: 1px solid #ccc;
    border-radius: 5px;
  }
  
  /* Button */
  .signup-btn {
    width: 100%;
    background-color: #1b408d;
    color: white;
    padding: 12px;
    font-size: 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 10px;
    transition: 0.3s;
  }
  
  .signup-btn:hover {
    background-color: #163b7a;
  }
  
  /* Login Text */
  .login-text {
    margin-top: 15px;
    font-size: 14px;
  }
  
  .login-link {
    color: #1b408d;
    text-decoration: none;
    font-weight: bold;
  }
  
  .login-link:hover {
    text-decoration: underline;
  }
  </style>
  