import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import SignupView from "../views/SignupView.vue";
import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ArchivedChatsView from "../views/ArchivedChatsView.vue";

const routes = [
  {
    path: "/",
    component: HomeView,
  },
  {
    path: "/signup",
    component: SignupView,
  },
  {
    path: "/login",
    component: LoginView,
  },
  {
    path: "/dashboard",
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: "/archived-chats",
    component: ArchivedChatsView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  if (to.meta.requiresAuth && !token) {
    next("/login"); // Redirect to login if not authenticated
  } else {
    next();
  }
});

export default router;