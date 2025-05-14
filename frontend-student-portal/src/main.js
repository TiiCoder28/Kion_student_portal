import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'

const app = createApp(App)
axios.defaults.baseURL = 'http://localhost:5000'
axios.defaults.withCredentials = true

window.MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      processEscapes: true
    },
    startup: {
      typeset: false
    }
  }
  
  // Load MathJax
  const mathJaxScript = document.createElement('script')
  mathJaxScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
  mathJaxScript.async = true
  document.head.appendChild(mathJaxScript)
  
  // Load KaTeX
  const katexScript = document.createElement('script')
  katexScript.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js'
  katexScript.async = true
  
  const katexStyle = document.createElement('link')
  katexStyle.rel = 'stylesheet'
  katexStyle.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css'
  
  katexScript.onload = () => document.head.appendChild(katexStyle)
  document.head.appendChild(katexScript)

app.use(createPinia())
app.use(router)

app.mount('#app')
