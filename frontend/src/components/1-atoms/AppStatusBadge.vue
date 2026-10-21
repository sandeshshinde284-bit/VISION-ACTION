<template>
  <span
    class="font-mono px-2 py-0.5 text-xs rounded-full font-semibold ring-1 ring-inset"
    :class="statusStyles"
  >
    {{ status }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  status: string;
}>();

const statusStyles = computed(() => {
  switch (props.status) {
    case 'Connected':
      return 'bg-green-500/10 text-green-400 ring-green-500/20';
    case 'Connecting...':
      return 'bg-yellow-500/10 text-yellow-400 ring-yellow-500/20';
    default: // Disconnected, Error
      return 'bg-red-500/10 text-red-400 ring-red-500/20';
  }
});
</script>
