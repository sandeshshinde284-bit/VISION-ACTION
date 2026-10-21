<!-- /frontend/src/components/2-molecules/SmartButton.vue -->
<template>
  <div class="smart-button-wrapper mt-3 ml-4 md:ml-6 select-none animate-fade-in font-sans">
    <!-- 1. Initial State: Action Trigger Button -->
    <div v-if="state === 'IDLE'" class="flex items-center space-x-2">
      <button
        @click="fetchTickets"
        class="flex items-center space-x-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-[11px] uppercase tracking-wider rounded-xl shadow-md hover:scale-[1.03] active:scale-[0.97] transition-all cursor-pointer border-none"
      >
        <span>{{ payload.label || 'Fetch Live ADO Tickets' }} ({{ payload.keyword }})</span>
      </button>
    </div>

    <!-- 2. Loading State: Spinning tactile icon -->
    <div v-else-if="state === 'LOADING'" class="flex items-center space-x-3 text-slate-500 text-xs font-bold animate-pulse">
      <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>V.I.S.I.O.N. is querying Azure DevOps live board...</span>
    </div>

    <!-- 3. Error State: Custom error prompt with retry handler -->
    <div v-else-if="state === 'ERROR'" class="flex flex-col space-y-2 max-w-md p-4 border border-rose-500/15 rounded-2xl bg-rose-500/5">
      <div class="flex items-center space-x-2 text-rose-500 text-xs font-bold">
        <span>⚠️</span>
        <span class="uppercase tracking-wider">ADO Fetch Failed</span>
      </div>
      <p class="text-[11px] text-slate-500 leading-normal">{{ errorMessage }}</p>
      <div class="flex space-x-2 pt-1">
        <button
          @click="fetchTickets"
          class="px-3.5 py-1.5 bg-rose-600/10 hover:bg-rose-600/20 text-rose-500 font-bold text-[10px] uppercase tracking-wider rounded-lg transition-all cursor-pointer border border-solid border-rose-500/20"
        >
          Retry Search
        </button>
        <button
          @click="state = 'IDLE'"
          class="px-3.5 py-1.5 bg-slate-500/10 hover:bg-slate-500/20 text-slate-500 font-bold text-[10px] uppercase tracking-wider rounded-lg transition-all cursor-pointer border border-none"
        >
          Dismiss
        </button>
      </div>
    </div>

    <!-- 4. Success State: Interactive Inline Tickets Grid -->
    <div v-else-if="state === 'SUCCESS'" class="flex flex-col space-y-3 w-full max-w-[98%] select-text">
      <!-- Success Header Stats Ribbon -->
      <div class="flex items-center justify-between p-3.5 border border-solid border-emerald-500/15 rounded-2xl bg-emerald-500/5">
        <div class="flex items-center space-x-2 text-emerald-500 text-xs font-bold">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span class="uppercase tracking-wider">Live ADO Tickets Retrieved</span>
        </div>
        <div class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
          Total: <span class="font-extrabold text-emerald-500">{{ tickets.length }}</span> matches
        </div>
      </div>

      <!-- Compact Colored Tickets Table -->
      <div v-if="tickets.length > 0" class="overflow-hidden border border-solid border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm bg-white dark:bg-[#0d1117]/30 max-h-[350px] overflow-y-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-900/40 border-b border-solid border-slate-200 dark:border-slate-800 select-none">
              <th class="p-3.5 font-bold text-slate-500 uppercase tracking-wider w-[10%]">ID</th>
              <th class="p-3.5 font-bold text-slate-500 uppercase tracking-wider w-[15%]">Type</th>
              <th class="p-3.5 font-bold text-slate-500 uppercase tracking-wider w-[50%]">Title</th>
              <th class="p-3.5 font-bold text-slate-500 uppercase tracking-wider w-[15%]">State</th>
              <th class="p-3.5 font-bold text-slate-500 uppercase tracking-wider w-[10%]">Assignee</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-solid divide-slate-100 dark:divide-slate-800/60">
            <tr v-for="ticket in tickets" :key="ticket.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-900/20 transition-colors">
              <td class="p-3.5 font-mono text-slate-400 font-semibold">
                <a :href="ticket.url" target="_blank" class="text-blue-500 hover:text-blue-600 font-bold hover:underline transition-all">#{{ ticket.id }}</a>
              </td>
              <td class="p-3.5">
                <span
                  class="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wider select-none border border-solid"
                  :class="getTypeClass(ticket.workItemType)"
                >
                  {{ ticket.workItemType }}
                </span>
              </td>
              <td class="p-3.5 font-medium text-slate-700 dark:text-slate-300 break-words leading-relaxed">{{ ticket.title }}</td>
              <td class="p-3.5">
                <span
                  class="px-2 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wider select-none border border-solid"
                  :class="getStateClass(ticket.state)"
                >
                  {{ ticket.state }}
                </span>
              </td>
              <td class="p-3.5 font-medium text-slate-400 dark:text-slate-500">{{ ticket.assignedTo || 'Unassigned' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="text-center p-6 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-slate-400 text-xs font-medium">
        No active open tickets found matching project '{{ payload.keyword }}' on Azure DevOps.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Ticket {
  id: number;
  workItemType: string;
  title: string;
  state: string;
  assignedTo: string;
  url: string;
}

const props = defineProps<{
  payload: {
    action_type: string;
    keyword: string;
    label?: string;
  }
}>();

const state = ref<'IDLE' | 'LOADING' | 'SUCCESS' | 'ERROR'>('IDLE');
const tickets = ref<Ticket[]>([]);
const errorMessage = ref('');

// Simple local frontend cache object with 3-minute TTL (Improvement #1)
const cache: Record<string, { data: Ticket[]; expiry: number }> = {};

const fetchTickets = async () => {
  state.value = 'LOADING';
  const kw = props.payload.keyword.trim();

  // 1. Check Frontend Local Cache
  const now = Date.now();
  if (cache[kw] && cache[kw].expiry > now) {
    // Serving from local cache (0ms latency)
    tickets.value = cache[kw].data;
    state.value = 'SUCCESS';
    return;
  }

  // 2. Perform REST fetch over unified relative API gateway
  try {
    const res = await fetch(`/api/ado/tickets?keyword=${encodeURIComponent(kw)}`);
    const data = await res.json();

    if (data.status === 'success') {
      tickets.value = data.data?.tickets || [];

      // Store in Cache (3-minute TTL)
      cache[kw] = {
        data: tickets.value,
        expiry: Date.now() + 3 * 60 * 1000
      };

      state.value = 'SUCCESS';
    } else {
      errorMessage.value = data.error?.message || 'The system was unable to pull tickets. Ensure your credentials are active.';
      state.value = 'ERROR';
    }
  } catch (err: any) {
    errorMessage.value = 'Network connectivity error timed out while connecting to the proxy REST gateway.';
    state.value = 'ERROR';
  }
};

// Colored state helpers
const getTypeClass = (type: string) => {
  const t = type.toLowerCase();
  if (t === 'bug') {
    return 'bg-red-500/10 border-red-500/20 text-red-400';
  } else if (t === 'feature' || t === 'epic') {
    return 'bg-purple-500/10 border-purple-500/20 text-purple-400';
  } else {
    return 'bg-blue-500/10 border-blue-500/20 text-blue-400';
  }
};

const getStateClass = (stateStr: string) => {
  const s = stateStr.toLowerCase();
  if (s === 'active' || s === 'in progress' || s === 'doing') {
    return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
  } else if (s === 'new' || s === 'to do') {
    return 'bg-sky-500/10 border-sky-500/20 text-sky-400';
  } else {
    return 'bg-slate-500/10 border-slate-500/20 text-slate-400';
  }
};
</script>
