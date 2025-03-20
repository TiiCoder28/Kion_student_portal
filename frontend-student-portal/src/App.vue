<script setup>
  import HomeView from './views/HomeView.vue'
  import LoginView from './views/LoginView.vue';
  import SignupView from './views/SignupView.vue';
  import DashboardView from './views/DashboardView.vue';
</script>

<template>
  <HomeView />
  <DashboardView />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background-color: #f9f9f9;
}
</style>