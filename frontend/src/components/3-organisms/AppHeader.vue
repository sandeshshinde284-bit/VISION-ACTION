<template>
  <header class="text-center mb-8">
    <h1 class="text-4xl sm:text-5xl font-bold text-cyan-400 tracking-wide">J.A.R.V.I.S. HUD</h1>
    <p class="mt-2 text-gray-500 flex items-center justify-center gap-2">
      <span>Status:</span>
      <AppStatusBadge :status="status" />
    </p>
  </header>
</template>

<script setup lang="ts">
import AppStatusBadge from '@/components/1-atoms/AppStatusBadge.vue';

defineProps<{
  status: string;
}>();
</script>
