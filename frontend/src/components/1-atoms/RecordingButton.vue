<!-- /frontend/src/components/1-atoms/RecordingButton.vue -->
<template>
  <button
    :disabled="disabled"
    @click="$emit('click')"
    class="relative flex items-center justify-center w-16 h-16 rounded-full transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
    :class="isRecording ? 'bg-red-500 shadow-lg shadow-red-500/50' : 'bg-cyan-600 hover:bg-cyan-500'"
  >
    <!-- The pulsing outer ring, only visible when recording -->
    <span v-if="isRecording" class="absolute h-full w-full rounded-full bg-red-400 opacity-75 animate-ping"></span>

    <!-- The microphone icon -->
    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
  </button>
</template>

<script setup lang="ts">
// This component receives its state as props from its parent.
// This makes it a "dumb" component, which is good practice for atoms.
defineProps<{
  isRecording: boolean;
  disabled: boolean;
}>();

// This defines the custom event the component can emit.
defineEmits(['click']);
</script>
