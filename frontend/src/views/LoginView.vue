<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-[#05070a] text-slate-100 font-sans select-none overflow-hidden">

    <!-- Premium, glowing abstract background blur nodes -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[var(--accent)]/5 blur-[120px] pointer-events-none animate-pulse"></div>
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none animate-pulse"></div>

    <!-- Main Glassmorphic Login Card -->
    <div class="relative w-full max-w-sm mx-4 bg-[#0d1117]/85 border border-slate-800/80 rounded-3xl p-6 md:p-8 backdrop-blur-3xl shadow-[0_0_50px_rgba(0,136,255,0.03)] border-b-slate-700/50 flex flex-col items-center">

      <!-- V.I.S.I.O.N. Cybernetic Holographic Core Logo -->
      <div class="relative w-20 h-20 mb-6 flex items-center justify-center select-none">

        <!-- Outer Spinning Dashed Geometric Ring -->
        <svg class="absolute w-full h-full animate-[spin_16s_linear_infinite] opacity-50" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="46" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="10 8" />
        </svg>

        <!-- Inner Pulsing Glow Node -->
        <div class="absolute w-12 h-12 rounded-full bg-[var(--accent)]/10 blur-[10px] animate-pulse"></div>

        <!-- Middle Glassmorphic Shield -->
        <div class="absolute w-14 h-14 rounded-full bg-[#05070a]/90 border border-slate-800/80 flex items-center justify-center shadow-[inset_0_0_12px_rgba(0,136,255,0.2)]">

          <!-- Holographic "V" Core vector path -->
          <svg class="w-6 h-6 text-[var(--accent)] drop-shadow-[0_0_8px_rgba(0,136,255,0.8)] opacity-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 3l7 18 7-18" />
          </svg>

          <!-- Pinging Active Neural Core Dot -->
          <span class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex h-2 w-2 mt-0.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>

      </div>

      <!-- Header Labels -->
      <h1 class="text-xs font-black uppercase tracking-[0.4em] text-[var(--accent)] drop-shadow-[0_0_10px_var(--accent)] mb-1">
        V.I.S.I.O.N.
      </h1>
      <p class="text-[8.5px] font-bold uppercase tracking-[0.25em] text-slate-500 mb-8 select-none text-center leading-relaxed max-w-[240px]">
        Virtual Intelligent System &amp; Platform Mentor
      </p>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="w-full flex flex-col space-y-4">

        <!-- Login ID Input Field -->
        <div class="flex flex-col space-y-1.5">
          <label class="text-[8.5px] font-black uppercase tracking-widest text-slate-500 px-1">
            Login ID / Name
          </label>
          <input
            v-model="username"
            type="text"
            class="w-full h-10 px-4 rounded-xl bg-[#05070a]/90 border border-slate-800 focus:border-[var(--accent)]/50 focus:shadow-[0_0_12px_rgba(0,136,255,0.08)] outline-none text-[11px] font-bold text-center tracking-widest transition-all duration-300"
            required
          />
        </div>

        <!-- Password Input Field -->
        <div class="flex flex-col space-y-1.5">
          <label class="text-[8.5px] font-black uppercase tracking-widest text-slate-500 px-1">
            Password
          </label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full h-10 px-4 rounded-xl bg-[#05070a]/90 border border-slate-800 focus:border-[var(--accent)]/50 focus:shadow-[0_0_12px_rgba(0,136,255,0.08)] outline-none text-[11px] font-bold text-center tracking-[0.2em] transition-all duration-300"
            required
          />
        </div>

        <!-- Error Feedback message -->
        <div v-if="error" class="text-[9px] font-bold uppercase tracking-widest text-red-400 text-center animate-pulse">
          ❌ Access Key Rejected
        </div>

        <!-- Submit pill key -->
        <button
          type="submit"
          class="w-full h-10 rounded-xl bg-[var(--accent)] text-[#05070a] text-[10px] font-black uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 shadow-[0_0_15px_rgba(0,136,255,0.2)] cursor-pointer"
        >
          Initialize Console Link
        </button>
      </form>

      <!-- Footer Branding -->
      <!-- <div class="mt-8 text-[7.5px] font-bold uppercase tracking-widest text-slate-600 select-none">
        VISION
      </div> -->

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const username = ref('');
const password = ref('');
const error = ref(false);

const handleLogin = async () => {
  error.value = false;
  
  const userName = username.value.trim();
  const userPass = password.value.trim();

  try {
    // Dynamic, port-aware local network bridge
    const baseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
      ? 'http://127.0.0.1:8000' 
      : window.location.origin;

    const res = await fetch(`${baseUrl}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: userName, password: userPass })
    });

    if (res.status === 200) {
      const data = await res.json();
      if (data.status === 'success') {
        const validatedName = data.username;
        const role = data.role;

        // Dynamic, secure server-side role and session mapping
        sessionStorage.setItem('vision_admin_name', validatedName);
        sessionStorage.setItem('vision_role', role);
        sessionStorage.setItem('vision_auth_token', data.token); // Secure DB-Driven Session Token!

        router.push('/');
        return;
      }
    }

    // Access Rejected
    error.value = true;
    password.value = '';
  } catch (err) {
    console.error("Login: Server connection failed:", err);
    error.value = true;
    password.value = '';
  }
};
</script>
