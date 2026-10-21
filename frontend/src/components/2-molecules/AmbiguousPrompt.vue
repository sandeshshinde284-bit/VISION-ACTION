<!-- /frontend/src/components/2-molecules/AmbiguousPrompt.vue -->
<template>
  <div class="ambiguous-prompt-wrapper mt-3 ml-4 md:ml-6 select-none animate-fade-in font-sans max-w-md p-4.5 border border-solid border-blue-500/15 rounded-2xl bg-blue-500/5">
    <!-- Header Prompt Section -->
    <div class="flex items-center space-x-2 text-blue-500 text-xs font-bold mb-3">
      <span>🤔</span>
      <span class="uppercase tracking-wider">Intent Clarification Required</span>
    </div>
    
    <p class="text-[11.5px] text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
      I found multiple matches in our ecosystem. To provide the most helpful response, what exactly are you looking for?
    </p>

    <!-- Options Button Deck -->
    <div class="flex flex-col space-y-2">
      <button
        v-for="opt in payload.options"
        :key="opt.intent"
        @click="selectOption(opt.intent)"
        class="w-full text-left p-3 rounded-xl border border-solid border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d1117]/30 hover:border-blue-500/40 hover:bg-blue-500/5 transition-all cursor-pointer flex items-start space-x-3 active:scale-[0.98]"
      >
        <div class="flex flex-col space-y-1">
          <span class="text-xs font-bold text-slate-800 dark:text-slate-200">{{ opt.label }}</span>
          <span class="text-[10px] text-slate-400 dark:text-slate-500 font-medium">{{ opt.description }}</span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWebSocket } from '@/composables/useWebSocket';

interface ClarificationOption {
  intent: string;
  label: string;
  description: string;
}

const props = defineProps<{
  payload: {
    type: string;
    message_id: string;
    confidence: number;
    reason: string;
    options: ClarificationOption[];
  }
}>();

// Grab global WebSocket controllers
const { sendMessage } = useWebSocket();

const selectOption = (intent: string) => {
  // Extract the original prompt or last searched topic from the reason or session context.
  // We can inject a forced [SCOPE: ...] tag over the original query!
  let originalQuery = "Oyster"; // Fallback default
  const reasonText = props.payload.reason.toLowerCase();
  
  // Try to parse the keyword from the reason text, e.g. "Query mentions 'Oyster'"
  const match = reasonText.match(/'(.*?)'/);
  if (match && match[1]) {
    originalQuery = match[1];
  }

  // Inject a clean [SCOPE: ...] metadata tag to force backend routing!
  if (intent === "EXPLICIT_ADO") {
    // Correct scope mapping: explicitly query ADO bypassing classifier entirely
    sendMessage(`[SCOPE: EXPLICIT_ADO] ${originalQuery}`);
  } else {
    sendMessage(`[SCOPE: ${intent}] ${originalQuery}`);
  }
};
</script>
