<!-- /frontend/src/components/2-molecules/visionCore.vue -->
<template>
  <div 
    class="relative flex items-center justify-center w-full aspect-square max-w-[450px] mx-auto"
  >
    <!-- 1. DECORATIVE HORIZONTAL LINES -->
    <div class="absolute inset-0 flex flex-col justify-center space-y-8 opacity-10 pointer-events-none">
       <div v-for="i in 6" :key="i" 
            class="w-[150%] h-[0.5px] bg-[var(--accent)] -translate-x-[25%]"
            :style="{ opacity: (1 - Math.abs(i-3)/3) * 0.5 }">
       </div>
    </div>

    <!-- 2. RADIATING VERTICAL TICKS -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
       <div v-for="i in 24" :key="i" 
            class="absolute w-[1px] h-4 bg-[var(--accent)]"
            :style="{ transform: `rotate(${i * 15}deg) translateY(-180px)` }">
       </div>
    </div>

    <!-- 3. CONCENTRIC CINEMATIC RINGS -->
    <div class="absolute inset-0 border border-[var(--accent)]/10 rounded-full"></div>
    <div class="absolute inset-10 border border-[var(--accent)]/20 rounded-full animate-spin-slow"></div>
    <div class="absolute inset-20 border border-dashed border-[var(--accent)]/10 rounded-full animate-spin-reverse"></div>

    <!-- 4. THE GLOWING CORE (Arc Reactor / Neural Lens) -->
    <div 
      class="relative w-48 h-48 rounded-full flex items-center justify-center transition-all duration-1000"
      :style="{ boxShadow: state === 'STANDBY' ? 'none' : `0 0 50px var(--core-glow)` }"
      :class="state === 'THINKING' ? 'animate-pulse' : ''"
    >
       <!-- INNER INTENSE BLUR -->
       <div 
         class="absolute w-24 h-24 rounded-full blur-2xl transition-colors duration-1000 opacity-40"
         :class="[
           state === 'STANDBY' ? 'bg-[var(--accent)]/10' : '',
           state === 'LISTENING' ? 'bg-red-500/30' : '',
           state === 'THINKING' ? 'bg-[var(--text-primary)]/20' : '',
           state === 'SPEAKING' ? 'bg-[var(--accent)]/40' : '',
         ]"
       ></div>

       <!-- THE CENTRAL IRIS -->
       <div 
         class="relative w-32 h-32 rounded-full border-2 flex flex-col items-center justify-center transition-all duration-700 shadow-sm"
         :style="{ borderColor: 'var(--border)', backgroundColor: 'var(--bg-panel)' }"
         :class="[
           state === 'LISTENING' ? 'border-red-500/60 shadow-[0_0_20px_rgba(239,68,68,0.2)]' : '',
           state === 'SPEAKING' ? 'border-[var(--accent)]' : '',
         ]"
       >
         <!-- Inner Tech Pattern -->
         <div class="absolute inset-4 border border-[var(--text-primary)] opacity-5 rounded-full"></div>
         <div class="absolute inset-8 border border-[var(--text-primary)] opacity-5 rounded-full"></div>

         <!-- THE CORE LIGHT SOURCE -->
         <div 
           class="w-10 h-10 rounded-full transition-all duration-500 z-20 shadow-sm"
           :style="{ backgroundColor: 'var(--core-iris)', boxShadow: state === 'STANDBY' ? 'none' : `0 0 20px var(--core-iris)` }"
           :class="[
             state === 'LISTENING' ? 'animate-pulse !bg-red-500 !shadow-red-500' : '',
           ]"
         ></div>
       </div>
    </div>

    <!-- 5. EXTENDING LINES -->
    <div class="absolute left-[-20%] right-[-20%] h-px bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent pointer-events-none"></div>

  </div>
</template>

<script setup lang="ts">
defineProps<{
  state: 'STANDBY' | 'LISTENING' | 'THINKING' | 'SPEAKING';
}>();
</script>
