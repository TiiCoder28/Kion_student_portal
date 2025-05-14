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
            <input type="email" placeholder="Confirm Email Address" v-model="confirmEmail" required />
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
            <input type="tel" placeholder="Phone Number" v-model="phoneNumber" required class="phone-input" />
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

          <div class="password-group">
            <input :type="showConfirmPassword ? 'text' : 'password'" 
                   placeholder="Confirm Password" 
                   v-model="confirmPassword" 
                   required />
            <span class="toggle-password" @click="showConfirmPassword = !showConfirmPassword">
              {{ showConfirmPassword ? '👁️' : '👁️‍🗨️' }}
            </span>
          </div>

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
  import { ref, onMounted } from "vue";
  import axios from "axios";
  import { useRouter } from "vue-router";
  
  const firstName = ref("");
  const lastName = ref("");
  const email = ref("");
  const confirmEmail = ref("");
  const phoneNumber = ref("");
  const countryCode = ref("ZA");
  const password = ref("");
  const confirmPassword = ref("");
  const authMethod = ref("email");
  const countries = ref([]);
  const showPassword = ref(false);
  const showConfirmPassword = ref(false);
  const router = useRouter();
  
const getEmojiFlag = (countryCode) => {
  return String.fromCodePoint(...[...countryCode.toUpperCase()].map(c => 0x1F1A5 + c.charCodeAt(0)));
};

  // Fetch country codes from an API
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
  
  const handleSignup = async () => {
    // Basic validation
    if (authMethod.value === 'email' && email.value !== confirmEmail.value) {
      alert("Emails do not match!");
      return;
    }
    if (password.value !== confirmPassword.value) {
      alert("Passwords do not match!");
      return;
    }
  
    try {
      const payload = {
        first_name: firstName.value,
        last_name: lastName.value,
        password: password.value
      };
  
      if (authMethod.value === 'email') {
        payload.email = email.value;
      } else {
        payload.phone_number = phoneNumber.value;
        payload.country_code = countryCode.value;
      }
  
      const response = await axios.post("http://localhost:5000/auth/signup", payload);
  
      if (response.status === 201) {
        const { access_token, user } = response.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("user", JSON.stringify(user));
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Signup error:", error.response?.data || error.message);
      alert(error.response?.data?.error || "Signup failed. Please try again.");
    }
  };
  </script>

  
  <style scoped>

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

  .heading {
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
    color: #666;
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
  margin-bottom: 8px 0;
}

.phone-input-group select {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.phone-input-group input {
  flex: 2;
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
  .signup-container {
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
  