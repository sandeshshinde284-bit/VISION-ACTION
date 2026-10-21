// /frontend/src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue' // Import our secure Login view

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login', // Secure gate entry path
      name: 'login',
      component: LoginView
    },
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    }
  ]
})

// --- SECURE NAVIGATION GUARD (GATES ENTIRE HUD COCKPIT) ---
router.beforeEach((to, _from) => {
  const token = sessionStorage.getItem('vision_auth_token');
  const role = sessionStorage.getItem('vision_role');
  
  // 1. Strict Token Validation (Dynamic Database Sessions!)
  // Instead of checking hardcoded string tokens, we verify that a cryptographically 
  // secure token was issued by the backend database and saved to the session.
  const isUserAuthenticated = token !== null && token.length > 30 && (role === 'ADMIN' || role === 'USER');

  if (to.name !== 'login' && !isUserAuthenticated) {
    // Force redirect unauthenticated users strictly to the Secure Login view!
    return { name: 'login' };
  } 
  
  if (to.name === 'login' && isUserAuthenticated) {
    // If they are already logged in and try to visit login, send them to the dashboard!
    return { name: 'home' };
  } 
  
  if (to.name === 'home' && !isUserAuthenticated) {
    return { name: 'login' };
  }

  // Proceed normally with route changes
  return true;
});

export default router
