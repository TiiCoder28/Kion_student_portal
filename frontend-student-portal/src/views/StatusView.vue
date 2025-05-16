<template>
    <transition name="fade">
      <div v-if="visible" 
           class="status-view-card"
           :class="{
             'status-success': type === 'success',
             'status-error': type === 'error'
           }">
        <div class="flex items-center justify-center">
          <span class="mr-2">
            <svg v-if="type === 'success'" class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <svg v-else class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </span>
          <span>{{ text }}</span>
        </div>
      </div>
    </transition>
</template>

<script setup>
  defineProps({
    text: String,
    type: String,
    visible: Boolean
  });
</script>

<style>
.status-view-card {
  position: fixed;
  top: 40px;
  right: 40px;
  min-width: 320px;
  max-width: 90vw;
  background: #fff;
  color: #333;
  border-radius: 10px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  padding: 2rem;
  z-index: 3000;
  border: 1.5px solid #e0e0e0;
  text-align: center;
  font-size: 1.1em;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-success {
  border-color: #7ed957;
}

.status-error {
  border-color: #e57373;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>