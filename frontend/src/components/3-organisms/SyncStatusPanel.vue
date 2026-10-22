<!-- /frontend/src/components/3-organisms/SyncStatusPanel.vue -->
<!--
  Sync Status Dashboard (ISSUES-TRACKER Issue #16 fix - 2026-10-22)

  Previously there was NO UI showing Confluence/ADO sync health at all - the
  user had to check backend logs manually. The backend side (/api/sync-status/summary)
  already existed but was completely unreachable: require_admin() called a method
  (security_service.is_admin()) that doesn't exist, so it always 403'd regardless
  of who called it (fixed separately in sync_status.py). This panel is the missing
  frontend half: it polls /api/sync-status/summary for the at-a-glance health cards,
  and shows the live sync_notification feed pushed over the WebSocket (Issue #5)
  underneath it.
-->
<template>
  <div class="w-full h-full flex flex-col overflow-hidden rounded-2xl border border-[var(--border)]/40 bg-[var(--bg-panel)]/80 backdrop-blur-xl shadow-xl">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]/30 shrink-0">
      <div class="flex items-center space-x-2">
        <span class="text-[var(--accent)]">🔄</span>
        <span class="font-black text-[12px] uppercase tracking-[0.2em] text-[var(--text-primary)]">Sync Status</span>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="fetchSummary"
          :disabled="isLoading"
          class="px-2.5 py-1 rounded-lg border border-[var(--border)]/40 text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/40 transition-all cursor-pointer disabled:opacity-40"
        >
          {{ isLoading ? '⟳ Refreshing...' : '🔄 Refresh' }}
        </button>
        <button @click="emit('close')" class="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm cursor-pointer" title="Close">✕</button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-4">
      <!-- Error state (e.g. not logged in, or a real server error) -->
      <div v-if="loadError" class="text-[11px] text-red-500 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3">
        ⚠️ {{ loadError }}
      </div>

      <!-- Source health cards -->
      <div v-if="summary" class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div
          v-for="source in ['confluence', 'ado']"
          :key="source"
          class="rounded-xl border border-[var(--border)]/30 bg-[var(--bg-primary)]/40 p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-bold text-[11px] uppercase tracking-wider text-[var(--text-primary)]">
              {{ source === 'confluence' ? '📘 Confluence' : '🎯 Azure DevOps' }}
            </span>
            <span
              class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider"
              :class="statusBadgeClass(summary[source]?.status)"
            >
              {{ summary[source]?.status || 'unknown' }}
            </span>
          </div>
          <div class="text-[11px] text-[var(--text-secondary)] space-y-1">
            <div>Last synced: <span class="text-[var(--text-primary)] font-semibold">{{ summary[source]?.last_synced || 'Never' }}</span></div>
            <div>Total syncs: <span class="text-[var(--text-primary)] font-semibold">{{ summary[source]?.total_syncs ?? 0 }}</span></div>
            <div v-if="summary[source]?.last_document">Last document: <span class="text-[var(--text-primary)] font-mono text-[10px]">{{ summary[source]?.last_document }}</span></div>
          </div>
        </div>
      </div>

      <div v-else-if="!loadError && isLoading" class="text-[11px] text-[var(--text-secondary)] italic text-center py-6">
        Loading sync status...
      </div>

      <!-- Live notification feed (fed by the WebSocket sync_notification frames) -->
      <div v-if="notifications && notifications.length > 0">
        <div class="text-[10px] font-black uppercase tracking-widest text-[var(--text-secondary)] mb-2">Recent Activity</div>
        <div class="space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar">
          <div
            v-for="(n, idx) in notifications"
            :key="idx"
            class="flex items-start space-x-2 text-[10.5px] px-3 py-2 rounded-lg"
            :class="n.status === 'success' ? 'bg-emerald-500/5 border border-emerald-500/20' : 'bg-red-500/5 border border-red-500/20'"
          >
            <span>{{ n.status === 'success' ? '✅' : '❌' }}</span>
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-[var(--text-primary)]">{{ n.source_system }} — {{ n.document_id }}</div>
              <div v-if="n.status !== 'success'" class="text-red-400 truncate">{{ n.error }}</div>
              <div v-else class="text-[var(--text-secondary)]">{{ n.chunk_count || 0 }} chunk(s), {{ n.vector_count || 0 }} vector(s)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const props = defineProps<{
  notifications?: any[]; // Pass useWebSocket()'s lastSyncNotifications through
}>();

const emit = defineEmits(['close']);

const summary = ref<any>(null);
const isLoading = ref(false);
const loadError = ref('');

const isLocal = window.location.href.indexOf('localhost') > -1 || window.location.href.indexOf('127.0.0.1') > -1;
const REST_BASE_URL = isLocal ? 'http://127.0.0.1:8000' : window.location.origin;

const fetchSummary = async () => {
  isLoading.value = true;
  loadError.value = '';
  try {
    const token = sessionStorage.getItem('vision_auth_token');
    const res = await fetch(`${REST_BASE_URL}/api/sync-status/summary`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (res.status === 401) {
      loadError.value = 'Session expired - please log in again to view sync status.';
      return;
    }
    if (!res.ok) {
      loadError.value = `Failed to load sync status (HTTP ${res.status}).`;
      return;
    }
    summary.value = await res.json();
  } catch (err) {
    loadError.value = 'Could not reach the sync status endpoint. Check your network connection.';
  } finally {
    isLoading.value = false;
  }
};

const statusBadgeClass = (status: string) => {
  switch (status) {
    case 'healthy': return 'bg-emerald-500/15 text-emerald-400';
    case 'syncing': return 'bg-blue-500/15 text-blue-400';
    case 'stale': return 'bg-amber-500/15 text-amber-400';
    case 'error': return 'bg-red-500/15 text-red-400';
    case 'not_configured': return 'bg-slate-500/15 text-slate-400';
    default: return 'bg-slate-500/15 text-slate-400';
  }
};

onMounted(fetchSummary);
</script>
