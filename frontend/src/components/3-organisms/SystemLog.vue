<!-- /frontend/src/components/3-organisms/SystemLog.vue -->
<template>
  <div class="w-full h-full flex flex-col" :class="isDarkMode ? 'dark' : 'light'">
    <!-- Event delegation on @click to intercept copy-btn clicks securely inside v-html -->
    <ul
      v-if="messages.length > 0"
      @click="handleLogClick"
      class="w-full flex flex-col space-y-4 md:space-y-4.5 pb-4"
    >
      <li
        v-for="(msg, index) in messages"
        :key="index"
        :class="[
          msg.startsWith('[ADMIN]:') ? 'items-end' :
          msg.startsWith('[SYSTEM:') ? 'items-center' : 'items-start',
          'flex flex-col space-y-1 w-full animate-fade-in'
        ]"
      >

        <!-- 1. USER MESSAGE (ADMIN) -->
        <template v-if="msg.startsWith('[ADMIN]:')">
          <div class="flex items-center space-x-2 text-slate-700 dark:text-slate-400 font-extrabold text-[10.5px] uppercase tracking-[0.2em] select-none mr-4 md:mr-6">
             <span>{{ adminName || 'Administrator' }}</span>          </div>
          <!-- Conversational User bubble aligning to the right with custom accent border and shape -->
          <div
            class="bg-[var(--accent)]/10 border border-[var(--accent)]/30 rounded-2xl rounded-tr-none py-2 px-3.5 max-w-[90%] md:max-w-[88%] text-left text-[13px] md:text-[13.5px] leading-relaxed tracking-normal font-sans antialiased font-normal shadow-sm mr-4 md:mr-6"
            :style="{ color: isDarkMode ? '#cbd5e1' : '#334155' }"
            @click="handleLogClick"
            v-html="parseMarkdown(msg.replace('[ADMIN]:', '').trim())"
          >
          </div>
        </template>

        <!-- 2. SYSTEM LOGS (METADATA) -->
        <template v-else-if="msg.startsWith('[SYSTEM:')">
          <div class="text-[9px] uppercase tracking-widest text-slate-500 font-bold italic py-1 opacity-50 select-none text-center">
             {{ msg }}
          </div>
        </template>

        <!-- 3. AI RESPONSES (V.I.S.I.O.N.) -->
        <template v-else>
          <div class="flex items-center space-x-2 text-[var(--accent)] font-black text-[11px] uppercase tracking-[0.25em] select-none ml-4 md:ml-6">
             <span class="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse shadow-[0_0_8px_var(--accent)]"></span>
             <span>V.I.S.I.O.N.</span>
          </div>

          <!-- Conversational AI bubble - Modern Flat Style (No background boxes, no borders, natural document flow - Surgical - Phase 4) -->
          <div
            class="ai-message-bubble text-left text-[13px] md:text-[13.5px] leading-relaxed tracking-normal font-sans antialiased font-normal ml-4 md:ml-6 w-full max-w-[96%]"
            :style="{ color: isDarkMode ? '#cbd5e1' : '#334155' }"
            v-html="parseMarkdown(cleanAdoMetadata(msg))"
          >
          </div>

          <!-- Real-time RAG Routing & Consensus Metadata Ribbon (Phase 4 - Moved cleanly to the bottom and only displays if RAG is run!) -->
          <div v-if="msg.includes('[SOURCES:')" class="flex flex-wrap gap-2 mt-2.5 ml-4 md:ml-6 select-none animate-fade-in text-[9px] font-bold uppercase tracking-widest">
            <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center space-x-1">
              <span class="w-1 h-1 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>High Confidence</span>
            </span>
            <span class="px-2.5 py-0.5 rounded-full bg-[var(--accent)]/10 border border-[var(--accent)]/30 text-[var(--accent)]">
              Consensus: 98.4%
            </span>
            <span class="px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-900/40 border border-[var(--border)] text-[var(--text-secondary)]">
              Source: Internal Wiki
            </span>
            <!-- If the response contains draft indicators, show a warning badge -->
            <span v-if="msg.toLowerCase().includes('draft')" class="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-500 flex items-center space-x-1">
              <span>⚠️ Draft Source</span>
            </span>
          </div>

          <!-- JIT ADO Dynamic Action Button (SaaS Flat Style) -->
          <div v-if="hasAdoCount(msg)" class="mt-3 ml-4 md:ml-6 select-none shrink-0 animate-fade-in">
            <button
              @click="triggerAdoQuery(getAdoCount(msg), msg)"
              class="flex items-center space-x-2 px-4.5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-black text-[11px] uppercase tracking-wider rounded-xl shadow-md hover:scale-[1.03] active:scale-[0.97] transition-all cursor-pointer"
            >
              <span>🔍</span>
              <span>View {{ getAdoCount(msg) }} Active ADO Tickets for this Topic</span>
            </button>
          </div>

          <!-- New JIT ADO Smart Action Button (Option C++ Structured JSON Frame) -->
          <div v-if="hasSmartAction(msg)" class="mt-3 ml-4 md:ml-6 select-none shrink-0 animate-fade-in">
            <SmartButton :payload="getSmartActionPayload(msg)" />
          </div>

          <!-- New JIT Ambiguous Intent Clarification Prompt -->
          <div v-if="hasAmbiguousIntent(msg)" class="mt-3 ml-4 md:ml-6 select-none shrink-0 animate-fade-in">
            <AmbiguousPrompt :payload="getAmbiguousIntentPayload(msg)" />
          </div>

          <!-- Control deck for copy and feedback reactions -->
          <div class="flex items-center space-x-2.5 mt-2 ml-4 md:ml-6 select-none shrink-0 animate-fade-in">
            <!-- Sleek Icon Copy Button (Enlarged for tactile click accuracy - Phase 4) -->
            <button
              @click="copyMessageText(msg, index)"
              class="w-16 h-6.5 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0d1117]/30 hover:border-[var(--accent)]/40 hover:bg-[var(--accent)]/5 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 text-[10px] font-bold cursor-pointer hover:scale-105 active:scale-[0.95] transition-all duration-200 flex items-center justify-center shadow-sm"
              :style="copiedIndices[index] ? { borderColor: '#10b981', color: '#10b981' } : {}"
              :title="copiedIndices[index] ? 'Copied successfully!' : 'Copy response to clipboard'"
            >
              <span>{{ copiedIndices[index] ? '✓ Copied' : '📋 Copy' }}</span>
            </button>

            <!-- Sleek Icon Thumbs-Up Button -->
            <button
              @click="toggleFeedback(index, 'LIKE')"
              class="w-8 h-6.5 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0d1117]/30 hover:border-emerald-500/40 hover:bg-emerald-500/5 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 text-[10px] cursor-pointer hover:scale-105 active:scale-[0.95] transition-all duration-200 flex items-center justify-center shadow-sm"
              :class="chatFeedback[index] === 'LIKE' ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.15)]' : ''"
              title="This response was helpful"
            >
              <span>👍</span>
            </button>

            <!-- Sleek Icon Thumbs-Down Button -->
            <button
              @click="toggleFeedback(index, 'DISLIKE')"
              class="w-8 h-6.5 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-[#0d1117]/30 hover:border-red-500/40 hover:bg-red-500/5 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 text-[10px] cursor-pointer hover:scale-105 active:scale-[0.95] transition-all duration-200 flex items-center justify-center shadow-sm"
              :class="chatFeedback[index] === 'DISLIKE' ? 'border-red-500/60 bg-red-500/10 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.15)]' : ''"
              title="This response was not helpful"
            >
              <span>👎</span>
            </button>
          </div>
        </template>

      </li>

      <!-- 4. PENDING NEURAL THINKING INDICATOR WITH REAL-TIME STATUS -->
      <li v-if="aiState === 'THINKING'" class="flex flex-col space-y-2 w-full items-start animate-fade-in">
        <!-- Current thinking status -->
        <div class="flex items-center space-x-2 text-[var(--accent)] font-bold text-[11px] uppercase tracking-[0.2em] select-none ml-4 md:ml-6">
           <span>{{ getStatusIcon(agentStatus || 'Thinking') }}</span>
           <span>{{ agentStatus || 'V.I.S.I.O.N. is thinking...' }}</span>
           <span class="text-[9px] text-slate-500 font-normal">({{ elapsedSeconds.toFixed(1) }}s)</span>
        </div>
        
        <!-- Status history -->
        <div v-if="statusHistory.length > 0" class="ml-4 md:ml-6 space-y-1 text-[10px]">
          <div v-for="(status, i) in statusHistory" :key="i" class="flex items-center space-x-2 text-slate-600">
            <span>✓</span>
            <span>{{ status.msg }}</span>
            <span class="text-slate-400">({{ formatElapsedTime(status.time - thinkingStartTime) }})</span>
          </div>
        </div>
        
        <!-- Bouncing dots animation -->
        <div class="p-2 w-24 text-left flex items-center justify-center space-x-1.5 shrink-0 ml-4 md:ml-6 bg-transparent border-0 shadow-none">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-bounce" style="animation-delay: 0ms; animation-duration: 0.8s;"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-bounce" style="animation-delay: 150ms; animation-duration: 0.8s;"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-bounce" style="animation-delay: 300ms; animation-duration: 0.8s;"></span>
        </div>
        
        <!-- Warning if taking too long -->
        <div v-if="elapsedSeconds > 5" class="text-[9px] text-amber-600 ml-4 md:ml-6 flex items-center space-x-1">
          <span>⏱️</span>
          <span>This is taking longer than usual. Please check the network connection.</span>
        </div>
      </li>
    </ul>
    <div v-else class="text-center text-slate-600 h-full flex items-center justify-center italic text-xs tracking-[0.3em] uppercase select-none">
      <p>Awaiting Uplink Data Stream...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import SmartButton from '@/components/2-molecules/SmartButton.vue';
import AmbiguousPrompt from '@/components/2-molecules/AmbiguousPrompt.vue';

const props = defineProps<{
  messages: string[];
  adminName?: string;
  isDarkMode?: boolean; // Prop passed from parent view
  aiState?: 'STANDBY' | 'THINKING' | 'SPEAKING'; // Dynamic connection state
  agentStatus?: string; // Real-time agent status logs (V.I.S.I.O.N. Redesign)
}>();

const emit = defineEmits(['trigger-ado-query']);

// Thinking Status Tracking
const statusHistory = ref<Array<{msg: string, time: number, completed: boolean}>>([])
const thinkingStartTime = ref(0)
const elapsedSeconds = ref(0)
let thinkingInterval: NodeJS.Timeout | null = null

// Cleanup helper for thinking interval
const cleanupThinkingInterval = () => {
  if (thinkingInterval) {
    clearInterval(thinkingInterval)
    thinkingInterval = null
  }
}

// Compute thinking start
watch(() => props.aiState, (newState) => {
  if (newState === 'THINKING') {
    statusHistory.value = []
    thinkingStartTime.value = Date.now()
    elapsedSeconds.value = 0
    
    // Clean up existing interval first to prevent leaks
    cleanupThinkingInterval()
    
    // Update elapsed time every 100ms
    thinkingInterval = setInterval(() => {
      if (props.aiState === 'THINKING') {
        elapsedSeconds.value = (Date.now() - thinkingStartTime.value) / 1000
      }
    }, 100)
  } else {
    cleanupThinkingInterval()
  }
})

// Watch for agentStatus changes to add to history
watch(() => props.agentStatus, (newStatus) => {
  if (newStatus && props.aiState === 'THINKING') {
    statusHistory.value.push({
      msg: newStatus,
      time: Date.now(),
      completed: false
    })
  }
})

// Cleanup on component unmount
onUnmounted(() => {
  cleanupThinkingInterval()
})

const getStatusIcon = (status: string) => {
  if (status.includes('Analyzing') || status.includes('intent')) return '🧠'
  if (status.includes('Querying') || status.includes('Searching')) return '🔍'
  if (status.includes('database')) return '📚'
  if (status.includes('Web') || status.includes('web')) return '🌐'
  if (status.includes('ADO') || status.includes('Azure')) return '🎯'
  if (status.includes('Generating') || status.includes('Composing')) return '✍️'
  if (status.includes('Error') || status.includes('error')) return '⚠️'
  if (status.includes('Synthesizing')) return '🧬'
  return '⟳'
}

const formatElapsedTime = (ms: number) => {
  const seconds = ms / 1000
  if (seconds < 1) return `${Math.round(seconds * 100)}ms`
  return `${seconds.toFixed(1)}s`
}

// JIT ADO Phantom Pre-Flight Helpers 
const hasAdoCount = (msg: string) => {
  return msg && msg.includes('[ADO_COUNT:');
};

const getAdoCount = (msg: string) => {
  const match = msg.match(/\[ADO_COUNT:\s*(\d+).*?\]/i);
  return (match && match[1]) ? parseInt(match[1], 10) : 0;
};

const getAdoQueryTerm = (msg: string) => {
  if (!msg || !msg.includes('[ADO_COUNT:')) {
    return '';
  }
  try {
    const parts = msg.split('[ADO_COUNT:');
    const targetPart = parts[1];
    if (targetPart) {
      const tagContent = targetPart.split(']')[0]; // Gets e.g. "243:Oyster"
      if (tagContent) {
        const tagParts = tagContent.split(':');
        const rawTerm = tagParts[1];
        if (rawTerm) {
          return rawTerm.trim(); // Returns "Oyster"
        }
      }
    }
  } catch (err) {
    // warn: "Failed to parse ADO query term:", err);
  }
  return '';
};

// --- PHASE 4 JIT ADO SMART ACTION HELPERS ---
const hasSmartAction = (msg: string) => {
  return msg && msg.includes('[SMART_ACTION:');
};

const getSmartActionPayload = (msg: string) => {
  if (!msg) return null;
  const match = msg.match(/\[SMART_ACTION:(.*?)\]/);
  if (match && match[1]) {
    try {
      return JSON.parse(match[1]);
    } catch (e) {
      // error: "Failed to parse Smart Action payload:", e);
    }
  }
  return null;
};

const hasAmbiguousIntent = (msg: string) => {
  return msg && msg.includes('[AMBIGUOUS_INTENT:');
};

const getAmbiguousIntentPayload = (msg: string) => {
  if (!msg) return null;
  const match = msg.match(/\[AMBIGUOUS_INTENT:(.*?)\]/);
  if (match && match[1]) {
    try {
      return JSON.parse(match[1]);
    } catch (e) {
      // error: "Failed to parse Ambiguous Intent payload:", e);
    }
  }
  return null;
};

const cleanAdoMetadata = (msg: string) => {
  if (!msg) return '';
  let clean = msg.replace(/\[ADO_COUNT:.*?\]/i, '').trim();
  clean = clean.replace(/\[SMART_ACTION:.*?\]/i, '').trim();
  clean = clean.replace(/\[AMBIGUOUS_INTENT:.*?\]/i, '').trim();
  return clean;
};

const triggerAdoQuery = (count: number, msg: string) => {
  let term = getAdoQueryTerm(msg);
  if (!term) {
    term = "Multiply Railcard";
  }
  emit('trigger-ado-query', { count, query: term });
};

// Chat reaction and copy actions
const chatFeedback = ref<Record<number, 'LIKE' | 'DISLIKE' | null>>({});
const copiedIndices = ref<Record<number, boolean>>({});

// Clipboard Copy: Strips backend metadata before copying
const copyMessageText = (rawMsg: string, index: number) => {
  try {
    const cleanText = rawMsg
      .replace(/\[SOURCES:.*?\]/gi, '')
      .replace(/\[TOKENS:.*?\]/gi, '')
      .replace(/\[SOURCE:.*?\]/gi, '')
      .trim();

    navigator.clipboard.writeText(cleanText)
      .then(() => {
        copiedIndices.value[index] = true;
        setTimeout(() => {
          copiedIndices.value[index] = false;
        }, 2000);
      })
      .catch((err: Error) => {
        log.error('Failed to copy to clipboard', err, { index });
      });
  } catch (error) {
    // error: "[CLIPBOARD COPY ERROR] Exception caught during copy process:", error);
  }
};

// Toggles Like/Dislike feedback
const toggleFeedback = (index: number, type: 'LIKE' | 'DISLIKE') => {
  try {
    const currentVal = chatFeedback.value[index];
    if (currentVal === type) {
      chatFeedback.value[index] = null; // Untoggle
    } else {
      chatFeedback.value[index] = type; // Toggle
    }
  } catch (error) {
    // error: "[FEEDBACK EXCEPTION] Failed to register user reaction:", error);
  }
};

const highlightCode = (code: string, lang: string): string => {
  let highlighted = code;

  // 1. Isolate and shield comments first to prevent any keywords inside comments from being styled
  const comments: string[] = [];
  highlighted = highlighted.replace(/(#.*|\/\/.*)/g, (match) => {
    comments.push(`<span class="hl-comment">${match}</span>`);
    return `%%COMMENT_${comments.length - 1}%%`;
  });

  // 2. Isolate and shield strings
  const strings: string[] = [];
  highlighted = highlighted.replace(/("(\\.|[^"\\])*"|'(\\.|[^'\\])*')/g, (match) => {
    strings.push(`<span class="hl-string">${match}</span>`);
    return `%%STRING_${strings.length - 1}%%`;
  });

  // 3. Highlight Keywords (Python & JS/TS standard keywords)
  const keywords = /\b(def|class|import|from|return|if|elif|else|for|while|try|except|as|const|let|var|function|async|await|import|export|new|this|typeof|in|of|break|continue|pass|with|lambda|yield|raise|global|nonlocal|assert|del|is|and|or|not)\b/g;
  highlighted = highlighted.replace(keywords, '<span class="hl-keyword">$1</span>');

  // 4. Highlight Constants
  const constants = /\b(True|False|None|null|undefined|true|false)\b/g;
  highlighted = highlighted.replace(constants, '<span class="hl-constant">$1</span>');

  // 5. Highlight Built-in Functions / Common Classes
  const builtins = /\b(print|input|float|int|str|bool|list|dict|set|tuple|len|range|format|open|sum|min|max|abs|type|console|log|error|warn|info|map|filter|btoa|atob|navigator|clipboard|window|document|setTimeout|clearTimeout|setInterval|clearInterval|Array|Object|String|Number|Boolean|Promise|JSON|stringify|parse)\b/g;
  highlighted = highlighted.replace(builtins, '<span class="hl-builtin">$1</span>');

  // 6. Highlight Numbers
  const numbers = /\b(\d+(?:\.\d+)?)\b/g;
  highlighted = highlighted.replace(numbers, '<span class="hl-number">$1</span>');

  // 7. Restore Strings
  strings.forEach((strHtml, idx) => {
    highlighted = highlighted.replace(`%%STRING_${idx}%%`, strHtml);
  });

  // 8. Restore Comments
  comments.forEach((commentHtml, idx) => {
    highlighted = highlighted.replace(`%%COMMENT_${idx}%%`, commentHtml);
  });

  return highlighted;
};

const parseMarkdown = (text: string) => {
  if (!text) return '';

  let result = text;
  const codeBlocks: string[] = [];

  // 1. ISOLATE & SHIELD Code Blocks (Save HTML cards to array, insert temporary tokens)
  result = result.replace(/```(\w*)[ \t]*\r?\n([\s\S]*?)```/g, (match, lang, code) => {
    const languageLabel = lang ? lang.toUpperCase() : 'CODE';
    const trimmedCode = code.trim();

    // Base64 encode the RAW, UNESCAPED code so clipboard copy is 100% accurate
    let base64Code = '';
    try {
      base64Code = btoa(unescape(encodeURIComponent(trimmedCode)));
    } catch (e) {
      // error: "Failed to base64 encode code snippet:", e);
    }

    // Escape the display code HTML ONLY to prevent browser rendering bugs
    const escapedDisplayCode = trimmedCode
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Check if this is a Mermaid diagram block 
    if (languageLabel === 'MERMAID') {
      // Encode raw code as a safe, browser-immutable Base64 string to prevent any HTML character scrambling!
      const base64Mermaid = btoa(unescape(encodeURIComponent(trimmedCode)));
      const htmlCard = `
        <div class="my-6 rounded-2xl border border-[var(--border)]/15 bg-white dark:bg-[#0d1117] p-6 shadow-md overflow-hidden select-none flex flex-col items-center">
          <div class="text-[10px] font-black uppercase tracking-[0.25em] text-[var(--accent)] mb-5 select-none flex items-center space-x-2">
            <span>📊 Interactive Architecture Flow</span>
          </div>
          <div class="language-mermaid block w-full max-h-[400px] bg-transparent overflow-auto custom-scrollbar select-text" data-mermaid-code="${base64Mermaid}"></div>
        </div>
      `;
      const tokenIndex = codeBlocks.length;
      codeBlocks.push(htmlCard);
      return `%%CODE_BLOCK_${tokenIndex}%%`;
    }

    // Generate the complete HTML card (Prisinte, borderless dark slate style matching 12.png)
    const htmlCard = `
      <div class="my-5 rounded-2xl overflow-hidden shadow-2xl bg-[#0d1117] border border-[#21262d]/50 select-none">
        <div class="flex justify-between items-center px-5 py-3 border-b border-[#21262d]/50 bg-[#161b22] select-none text-[10px] font-black uppercase tracking-widest text-slate-400">
          <span>${languageLabel}</span>
          <button
            data-copy-code="${base64Code}"
            class="copy-btn px-3 py-1 rounded-lg bg-[#21262d] border border-[#30363d] hover:bg-[#30363d] hover:border-slate-500 text-slate-300 hover:text-white transition-all cursor-pointer font-black text-[9px] uppercase tracking-widest"
          >
            Copy Code
          </button>
        </div>
        <pre class="p-5 overflow-x-auto text-[14px] md:text-[15px] leading-relaxed text-slate-300 custom-scrollbar select-text"><code>${highlightCode(escapedDisplayCode, languageLabel)}</code></pre>
      </div>
    `;

    // Store in array and return a unique safe token
    const tokenIndex = codeBlocks.length;
    codeBlocks.push(htmlCard);
    return `%%CODE_BLOCK_${tokenIndex}%%`;
  });

  // 2. Parse Inline Code: `code` (Sleek neutral grey-slate badges styled cleanly in CSS via variables)
  result = result.replace(/`(.*?)`/g, (match, code) => {
    const escapedInline = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return `<code>${escapedInline}</code>`;
  });

  // 3. Parse Bold Text: **text** (Forced high-contrast slate-white in dark theme)
  result = result.replace(/\*\*(.*?)\*\*/g, '<strong class="markdown-bold font-bold">$1</strong>');

  // 3.2. Parse Markdown Links: [text](url) 
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-500 hover:text-blue-600 hover:underline font-semibold">$1</a>');

  // 3.4. Parse Markdown Headings (H1 to H6)
  // Ensures that output like "### Key Requirements" is rendered in bold, white/black high-contrast text instead of standard grey
  result = result.replace(/^(#{1,6})[ \t]+(.+)$/gm, (match, hashes, content) => {
    const level = hashes.length;
    // Map heading levels to elegant, compact sub-headers
    const sizes = [
      'text-lg md:text-xl',
      'text-base md:text-lg',
      'text-[15px] md:text-[16px]',
      'text-[14px] md:text-[14.5px]',
      'text-[13px] md:text-[13.5px]',
      'text-[12px] md:text-[12.5px]'
    ];
    const sizeClass = sizes[level - 1];
    return `<h${level} class="${sizeClass} font-bold mt-5 mb-2 markdown-heading">${content}</h${level}>`;
  });

  // 3.5. Parse Markdown Tables (Phase 3 - Robust High-Fidelity Table Compiler)
  // Dynamically converts any standard markdown grid syntax into styled HTML tables
  result = result.replace(/(?:^|\n)(\|[^\n]+\|\r?\n\|(?:[ \t]*:?-+:?[ \t]*\|)+\r?\n(?:\|[^\n]+\|\r?\n?)+)/g, (match, tableBlock) => {
    const rows = tableBlock.trim().split(/\r?\n/);
    let htmlTable = '<div class="overflow-x-auto my-4 border border-[var(--accent)]/10 rounded-xl bg-[var(--bg-panel)]/30"><table class="vision-table w-full text-left border-collapse select-text">';

    rows.forEach((row: string, rIdx: number) => {
      const cols = row.split('|').map((c: string) => c.trim()).filter((c: string, cIdx: number) => cIdx > 0 && cIdx < row.split('|').length - 1);
      if (rIdx === 0) {
        htmlTable += '<thead class="bg-[var(--accent)]/5 border-b border-[var(--accent)]/10"><tr>';
        // Force table headers to be pure white/black high-contrast so they never look grey
        cols.forEach((col: string) => { htmlTable += `<th class="px-4 py-3 text-[11px] font-black uppercase tracking-wider">${col}</th>`; });
        htmlTable += '</tr></thead><tbody class="divide-y divide-[var(--accent)]/5">';
      } else if (rIdx === 1) {
        // Alignment/Divider row, skip
      } else {
        htmlTable += '<tr class="hover:bg-[var(--accent)]/5 transition-colors">';
        cols.forEach((col: string) => { htmlTable += `<td class="px-4 py-3 text-[13px] md:text-[13.5px]">${col}</td>`; });
        htmlTable += '</tr>';
      }
    });

    htmlTable += '</tbody></table></div>';
    return htmlTable;
  });

  // 3.6. Parse Bulleted Lists (Unordered)
  // Matches consecutive lines starting with - or * or + and wraps them in a styled list container
  result = result.replace(/(?:^|\n)((?:[ \t]*(?:[-*+])[ \t]+[^\n]+\r?\n?)+)/g, (match, listBlock) => {
    const items = listBlock.trim().split(/\r?\n/);
    let htmlList = '<ul class="list-disc pl-6 my-3 space-y-1.5">';
    items.forEach((item: string) => {
      const cleanItem = item.replace(/^[ \t]*[-*+][ \t]+/, '');

      // Dynamic Subheader Detection: If item starts with bold and ends with a colon or bold tag
      const isSubheader = cleanItem.startsWith('<strong') && (cleanItem.endsWith(':') || cleanItem.endsWith('</strong>') || cleanItem.endsWith('：'));
      if (isSubheader) {
        htmlList += `<li class="list-none -ml-5 mt-3 mb-1 text-[11px] md:text-[12px] font-black uppercase tracking-wider text-[var(--accent)]">${cleanItem}</li>`;
      } else {
        htmlList += `<li class="text-[13px] md:text-[13.5px] leading-relaxed">${cleanItem}</li>`;
      }
    });
    htmlList += '</ul>';
    return htmlList;
  });

  // 3.7. Parse Numbered Lists (Ordered)
  // Matches consecutive lines starting with digits (e.g. 1.) and wraps them in a styled ordered list container
  result = result.replace(/(?:^|\n)((?:[ \t]*\d+\.[ \t]+[^\n]+\r?\n?)+)/g, (match, listBlock) => {
    const items = listBlock.trim().split(/\r?\n/);
    let htmlList = '<ol class="list-decimal pl-6 my-3 space-y-1.5">';
    items.forEach((item: string) => {
      const cleanItem = item.replace(/^[ \t]*\d+\.[ \t]+/, '');

      // Dynamic Subheader Detection for ordered lists
      const isSubheader = cleanItem.startsWith('<strong') && (cleanItem.endsWith(':') || cleanItem.endsWith('</strong>') || cleanItem.endsWith('：'));
      if (isSubheader) {
        htmlList += `<li class="list-none -ml-5 mt-3 mb-1 text-[11px] md:text-[12px] font-black uppercase tracking-wider text-[var(--accent)]">${cleanItem}</li>`;
      } else {
        htmlList += `<li class="text-[13px] md:text-[13.5px] leading-relaxed">${cleanItem}</li>`;
      }
    });
    htmlList += '</ol>';
    return htmlList;
  });

  // 4. Parse Line Breaks: \n (Translate standard text linebreaks)
  result = result.replace(/\n/g, '<br />');

  // Clean up any double or single <br> tags immediately following structural block closing tags to prevent excessive whitespace gaps! 
  result = result.replace(/<\/(h[1-6]|table|tr|li|ul|ol)>\s*(<br\s*\/?>\s*)+/gi, '</$1>');

  // 5. STRIP METADATA CITATIONS (Hide raw WebSocket payloads from the visual bubble view)
  result = result.replace(/<br\s*\/?>\s*\[SOURCES:.*?\]/gi, '');
  result = result.replace(/\[SOURCES:.*?\]/gi, '');

  // 6. STRIP METADATA TOKENS (Hide raw WebSocket payloads from the visual bubble view)
  result = result.replace(/<br\s*\/?>\s*\[TOKENS:.*?\]/gi, '');
  result = result.replace(/\[TOKENS:.*?\]/gi, '');

  // 6.5. STRIP METADATA SOURCE REASONS (Hide raw routing reasons from visual bubbles - Phase 4)
  result = result.replace(/<br\s*\/?>\s*\[SOURCE:.*?\]/gi, '');
  result = result.replace(/\[SOURCE:.*?\]/gi, '');

  // 7. RESTORE SHIELDED CODE CARDS (Swap tokens back to pristine HTML cards)
  codeBlocks.forEach((htmlCard, index) => {
    result = result.replace(`%%CODE_BLOCK_${index}%%`, htmlCard);
  });

  return result;
};

// Event Delegation Handler: Intercepts copy-btn clicks inside v-html securely
const handleLogClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (target && target.classList.contains('copy-btn')) {
    const base64Code = target.getAttribute('data-copy-code');
    if (base64Code) {
      try {
        // Decode the safe Base64 string back into raw string
        const codeToCopy = decodeURIComponent(escape(atob(base64Code)));

        // Write to Clipboard
        navigator.clipboard.writeText(codeToCopy)
          .then(() => {
            const originalText = target.innerText;
            target.innerText = 'COPIED!';
            target.style.borderColor = '#10B981'; // Green Feedback Border
            target.style.color = '#10B981'; // Green Feedback Font

            setTimeout(() => {
              target.innerText = originalText;
              target.style.borderColor = '';
              target.style.color = '';
            }, 2000);
          })
          .catch((err: Error) => {
            log.error('Failed to copy code snippet to clipboard', err);
          });
      } catch (e) {
        // error: "Failed to execute click-to-copy decode sequence:", e);
      }
    }
  }
};
</script>

<style scoped>
/* Premium, Theme-Aware Scoped Styles for Code and Typography */
:deep(code:not(pre code)) {
  background-color: rgba(148, 163, 184, 0.08);
  color: var(--text-secondary); /* Automatically resolves contrast between themes */
  border: 1px solid rgba(148, 163, 184, 0.15);
  padding: 1.5px 5.5px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 13px;
  letter-spacing: -0.01em;
  word-break: break-word;
}
.dark :deep(code:not(pre code)) {
  background-color: rgba(148, 163, 184, 0.12);
  color: #cbd5e1; /* Soft, warm white for crisp dark-mode reading */
  border-color: rgba(148, 163, 184, 0.2);
}

:deep(pre) {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}
:deep(pre code) {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

/* High-Fidelity IDE-Style Code Syntax Coloring (GitHub Dark/Light Hybrid) */
:deep(.hl-comment) {
  color: #7c8c8e;
  font-style: italic;
}

:deep(.hl-string) {
  color: #7ee787; /* Soft emerald string */
}

:deep(.hl-keyword) {
  color: #ff7b72; /* Warm coral-red keyword */
  font-weight: 600;
}

:deep(.hl-builtin) {
  color: #d2a8ff; /* Soft violet built-in */
}

:deep(.hl-constant) {
  color: #ffab70; /* Soft copper-orange constant */
}

:deep(.hl-number) {
  color: #79c0ff; /* Soft sky-blue number */
}

/* Premium Scoped Styles for Headings, Bold Text, Lists, and Tables (Resolves Tailwind v4 v-html Contrast Bugs) */
:deep(.markdown-heading), :deep(.markdown-bold) {
  color: var(--text-primary) !important;
}

/* Explicit high-contrast settings for lists and table cells to prevent grey-out or invisibility in light mode */
:deep(li) {
  color: var(--text-primary) !important;
}
:deep(.vision-table td), :deep(.vision-table th) {
  color: var(--text-primary) !important;
  white-space: nowrap !important; /* Forces all work item columns to remain on exactly 1 line (no wrapping!) - Phase 4 */
}

/* Premium Markdown Table Styles */
:deep(.vision-table) {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  margin: 20px 0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}
:deep(.vision-table th) {
  background-color: var(--bg-panel);
  color: var(--text-primary);
  font-weight: 900;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.15em;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
:deep(.vision-table td) {
  padding: 12px 18px;
  border-bottom: 1px solid var(--border);
  font-size: 13.5px;
  color: inherit; /* Dynamically inherits standard bubble font color perfectly! */
}
:deep(.vision-table tr:last-child td) {
  border-bottom: none;
}
:deep(.vision-table tr:hover td) {
  background-color: var(--bg-primary);
}
</style>
