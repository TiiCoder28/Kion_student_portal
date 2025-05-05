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
              <div class="auth-method-toggle">
                <button type="button" :class="{ active: authMethod === 'email' }" @click="authMethod = 'email'">
                  Use Email
                </button>
                <button type="button" :class="{ active: authMethod === 'phone' }" @click="authMethod = 'phone'">
                  Use Phone
                </button>
              </div>

              <div v-if="authMethod === 'email'">
                <input type="email" placeholder="Email Address" v-model="email" required />
              </div>

              <div v-if="authMethod === 'phone'" class="phone-input-group">
                <select v-model="countryCode" required class="country-select">
              <option v-for="country in countries" 
                      :key="country.code" 
                      :value="country.code"
                      :selected="country.code === 'ZA'">
                {{ country.flag }} {{ country.name }} ({{ country.dial_code }})
              </option>
            </select>
                <input type="tel" placeholder="Phone Number" v-model="phoneNumber" required />
              </div>

            <div class="password-group">
              <input :type="showPassword ? 'text' : 'password'" 
                    placeholder="Password" 
                    v-model="password" 
                    required />
              <span class="toggle-password" @click="showPassword = !showPassword">
                {{ showPassword ? '👁️' : '👁️‍🗨️' }}
              </span>
          </div>
              
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
  import { ref, onMounted } from "vue";
  import axios from "axios";
  import { useRouter } from "vue-router";
  
  const email = ref("");
  const phoneNumber = ref("");
  const countryCode = ref("");
  const password = ref("");
  const authMethod = ref("email");
  const countries = ref([]);
  const showPassword = ref(false);
  const router = useRouter();
  
const getEmojiFlag = (countryCode) => {
  return String.fromCodePoint(...[...countryCode.toUpperCase()].map(c => 0x1F1A5 + c.charCodeAt(0)));
};

  // Same country code fetching as in Signup.vue
  onMounted(async () => {
  try {
    const response = await axios.get("https://restcountries.com/v3.1/all");
    
    countries.value = response.data
      .map(country => ({
        name: country.name.common,
        code: country.cca2,
        dial_code: country.idd?.root + (country.idd?.suffixes?.[0] || '') || '+27',
        flag: getEmojiFlag(country.cca2)
      }))
      .filter(c => c.dial_code)
      .sort((a, b) => a.name.localeCompare(b.name));

    
    countries.value = [
      {
        name: "South Africa",
        code: "ZA",
        dial_code: "+27",
        flag: "🇿🇦"
      },
      ...countries.value.filter(c => c.code !== 'ZA')
    ];
    
  } catch (error) {
    console.error("Failed to fetch countries:", error);
    countries.value = [
      { name: "South Africa", code: "ZA", dial_code: "+27", flag: "🇿🇦" },
      { name: "Lesotho", code: "LS"}
    ];
  }
});

  
  const handleLogin = async () => {
    try {
      const payload = {
        password: password.value
      };
  
      if (authMethod.value === 'email') {
        payload.email = email.value;
      } else {
        payload.phone_number = phoneNumber.value;
        payload.country_code = countryCode.value;
      }
  
      const response = await axios.post("http://localhost:5000/auth/login", payload);
  
      if (response.status === 200) {
        const { access_token, user } = response.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("user", JSON.stringify(user));
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
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
    padding: 20px;
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
  
  .auth-method-toggle {
  display: flex;
  margin-bottom: 15px;
  border: 1px solid #ccc;
  border-radius: 5px;
  overflow: hidden;
}

.auth-method-toggle button {
  flex: 1;
  padding: 10px;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
}

.auth-method-toggle button.active {
  background: #1b408d;
  color: white;
}

.phone-input-group {
  display: flex;
  gap: 10px;
  margin: 8px 0;
}

.phone-input-group select {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.phone-input-group input {
  flex: 1;
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

  .country-select {
  width: 120px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.phone-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

/* Password Input Group */
.password-group {
  position: relative;
  margin: 8px 0;
}

.password-group input {
  width: 100%;
  padding: 10px 40px 10px 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.toggle-password {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  user-select: none;
}

/* Responsive Design */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  
  .left-pane {
    display: none;
  }
  
  .right-pane {
    width: 100%;
    padding: 20px;
  }
  
  .form-container {
    width: 100%;
    max-width: 400px;
  }
  
  .phone-input-group {
    flex-direction: column;
  }
  
  .country-select {
    width: 100%;
  }
}
  </style>
  