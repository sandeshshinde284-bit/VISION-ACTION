<template>
  <section class="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-lg shadow-lg">
    <div class="p-5">
      <h2 class="text-lg font-semibold text-gray-300">WebSocket Echo Test</h2>
      <p class="text-sm text-gray-500 mt-1">Send a message to the backend and verify it gets echoed back.</p>
      <div class="flex items-center gap-3 mt-4">
        <input
          v-model="localMessage"
          @keyup.enter="handleSend"
          class="block w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-cyan-500 transition"
          placeholder="Type a message..."
        />
        <AppButton
          @click="handleSend"
          :disabled="!isMessageValid || disabled"
        >
          Send
        </AppButton>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import AppButton from '@/components/1-atoms/AppButton.vue';

const props = defineProps<{
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (e: 'send', message: string): void;
}>();

const localMessage = ref('');
const isMessageValid = computed(() => localMessage.value.trim() !== '');

const handleSend = () => {
  if (isMessageValid.value && !props.disabled) {
    emit('send', localMessage.value);
    localMessage.value = '';
  }
};
</script>
