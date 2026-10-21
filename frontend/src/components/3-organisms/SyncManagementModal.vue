<!-- /frontend/src/components/3-organisms/SyncManagementModal.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Types
interface SyncResult {
  document_id: string
  source_system: string
  sync_type: string
  status: 'COMPLETE' | 'IN_PROGRESS' | 'ERROR'
  chunk_count: number
  vector_count: number
  started_at: string
  completed_at?: string
  duration_seconds?: number
}

interface LastSyncInfo {
  source_system: string
  last_completed_at?: string
  last_status: string
  last_document?: string
  total_syncs: number
  successful_syncs: number
  failed_syncs: number
  minutes_since_last_sync?: number
}

interface SyncSummary {
  confluence: {
    last_synced: string
    status: 'healthy' | 'error' | 'syncing' | 'stale' | 'not_configured'
    total_syncs: number
    last_status?: string
  }
  ado: {
    last_synced: string
    status: 'healthy' | 'error' | 'syncing' | 'stale' | 'not_configured'
    total_syncs: number
    last_status?: string
  }
}

// State
const isOpen = ref(false)
const isLoading = ref(false)
const isSyncing = ref(false)
const isRefreshing = ref(false)
const syncingSystem = ref<'CONFLUENCE' | 'ADO' | null>(null)
const lastError = ref<string>('')
const errorTimeout = ref<NodeJS.Timeout | null>(null)
const refreshError = ref<boolean>(false)
const refreshAttempts = ref<number>(0)

// Module-level auto-refresh interval (prevents memory leak)
let autoRefreshInterval: NodeJS.Timeout | null = null

const summary = ref<SyncSummary | null>(null)
const confluenceLastSync = ref<LastSyncInfo | null>(null)
const adoLastSync = ref<LastSyncInfo | null>(null)
const syncHistory = ref<SyncResult[]>([])
const selectedTab = ref<'summary' | 'history' | 'confluence' | 'ado'>('summary')

// Form state
const syncType = ref<'page' | 'delta'>('delta')
const duration = ref(30)
const syncTarget = ref<'CONFLUENCE' | 'ADO' | 'both'>('CONFLUENCE')

const router = useRouter()

// Computed
const statusColor = computed(() => ({
  'COMPLETE': 'text-green-600',
  'IN_PROGRESS': 'text-blue-600',
  'ERROR': 'text-red-600',
  'NEVER': 'text-gray-400'
}))

const statusBadgeClass = computed(() => (status: string) => {
  const classes: Record<string, string> = {
    'COMPLETE': 'bg-green-100 text-green-800 flex items-center gap-1',
    'IN_PROGRESS': 'bg-blue-100 text-blue-800 flex items-center gap-1',
    'ERROR': 'bg-red-100 text-red-800 flex items-center gap-1',
    'healthy': 'bg-green-100 text-green-800 flex items-center gap-1',
    'error': 'bg-red-100 text-red-800 flex items-center gap-1',
    'syncing': 'bg-blue-100 text-blue-800 flex items-center gap-1',
    'stale': 'bg-yellow-100 text-yellow-800 flex items-center gap-1',
    'not_configured': 'bg-gray-100 text-gray-800 flex items-center gap-1'
  }
  // Use purple for unknown statuses (better visibility for debugging)
  return classes[status] || 'bg-purple-100 text-purple-800 flex items-center gap-1'
})

// Format duration to human-readable
const durationDisplay = computed(() => {
  const hours = (duration.value / 60).toFixed(1)
  const days = (duration.value / 1440).toFixed(2)
  if (duration.value < 60) return `${duration.value}m`
  if (duration.value < 1440) return `${hours}h (${duration.value}m)`
  return `${days}d`
})

// Format ISO date to local timezone
const formatLocalTime = (isoString?: string | null): string => {
  if (!isoString) return 'Never'
  try {
    const date = new Date(isoString)
    // Check for Invalid Date
    if (isNaN(date.getTime())) return 'Invalid date'
    return date.toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return 'Invalid date'
  }
}

// Get icon for status
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'COMPLETE': return '✓'
    case 'IN_PROGRESS': return '⟳'
    case 'ERROR': return '✗'
    case 'healthy': return '✓'
    case 'error': return '✗'
    case 'syncing': return '⟳'
    case 'stale': return '⚠'
    case 'not_configured': return '○'
    default: return '·'
  }
}

// Methods
async function loadSyncData() {
  isLoading.value = true
  // Prevent multiple simultaneous requests (race condition fix)
  if (isRefreshing.value) {
    isLoading.value = false
    return
  }
  isRefreshing.value = true

  try {
    // Load summary
    const summaryRes = await fetch('/api/sync-status/summary')
    if (summaryRes.ok) {
      const data = await summaryRes.json()
      // Validate API response structure
      if (data && data.confluence && data.ado) {
        summary.value = data
        refreshError.value = false
        refreshAttempts.value = 0
      } else {
        // error: 'Invalid API response structure:', data)
        refreshError.value = true
        refreshAttempts.value += 1
      }
    } else {
      refreshError.value = true
      refreshAttempts.value += 1
    }

    // Load last sync info
    const confRes = await fetch('/api/sync-status/last-sync/CONFLUENCE')
    if (confRes.ok) {
      confluenceLastSync.value = await confRes.json()
    }

    const adoRes = await fetch('/api/sync-status/last-sync/ADO')
    if (adoRes.ok) {
      adoLastSync.value = await adoRes.json()
    }

    // Load history (limit to 10 most recent)
    const histRes = await fetch('/api/sync-status/history?limit=10')
    if (histRes.ok) {
      syncHistory.value = await histRes.json()
    }
  } catch (error) {
    // error: 'Failed to load sync data:', error)
    refreshError.value = true
    refreshAttempts.value += 1
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

async function triggerSync() {
  if (!syncTarget.value) {
    showError('Please select a sync target (Confluence or ADO)')
    return
  }

  // Prevent multiple simultaneous syncs
  if (isSyncing.value) {
    showError('A sync is already running. Please wait for it to complete.')
    return
  }

  isSyncing.value = true
  syncingSystem.value = syncTarget.value

  try {
    let endpoint = ''
    switch (syncTarget.value) {
      case 'CONFLUENCE':
        if (syncType.value === 'delta') {
          endpoint = `/api/sync/confluence/delta?minutes=${duration.value}`
        } else {
          showError('Single page sync requires a page ID')
          return
        }
        break
      case 'ADO':
        if (syncType.value === 'delta') {
          endpoint = `/api/sync/ado/delta?days=${Math.ceil(duration.value / 24)}`
        } else {
          showError('Single item sync requires an item ID')
          return
        }
        break
    }

    const response = await fetch(endpoint, {
      method: 'POST'
    })

    if (response.ok) {
      const result = await response.json()
      const system = syncTarget.value === 'CONFLUENCE' ? 'Confluence' : 'Azure DevOps'
      showSuccess(`${system} sync queued successfully! Starting sync...`)
      
      // Refresh data after 2 seconds
      setTimeout(() => {
        loadSyncData()
      }, 2000)
    } else if (response.status === 403) {
      showError('Unauthorized: You do not have permission to trigger syncs')
    } else if (response.status === 429) {
      showError('Rate limit exceeded: Too many syncs in a short time. Please wait and try again.')
    } else {
      const error = await response.json()
      showError(`Sync failed: ${error.detail || 'Unknown error'}`)
    }
  } catch (error) {
    // error: 'Failed to trigger sync:', error)
    showError('Failed to trigger sync. Check browser console for details.')
  } finally {
    isSyncing.value = false
    syncingSystem.value = null
  }
}

function showError(message: string) {
  lastError.value = message
  if (errorTimeout.value !== null) {
    clearTimeout(errorTimeout.value)
    errorTimeout.value = null
  }
  errorTimeout.value = setTimeout(() => {
    lastError.value = ''
    errorTimeout.value = null
  }, 5000)
}

function showSuccess(message: string) {
  lastError.value = ''
  // Success: message logged
}

function openModal() {
  isOpen.value = true
  loadSyncData()
  
  // Clear any existing interval first (prevents multiple intervals)
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
  
  // Auto-refresh every 10 seconds while modal is open
  autoRefreshInterval = setInterval(() => {
    if (isOpen.value) {
      loadSyncData()
    }
  }, 10000)
}

function closeModal() {
  isOpen.value = false
  // Clean up interval when closing modal
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
}

function formatTime(isoTime?: string) {
  if (!isoTime) return 'Never'
  const date = new Date(isoTime)
  return date.toLocaleString()
}

function formatDuration(seconds?: number) {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  return `${(seconds / 60).toFixed(2)}m`
}

onMounted(() => {
  // Check if user is admin and can access sync UI
  // This will be checked by the backend on API calls
})

onUnmounted(() => {
  // Comprehensive cleanup on component unmount
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
  if (errorTimeout.value !== null) {
    clearTimeout(errorTimeout.value)
    errorTimeout.value = null
  }
})
</script>

<template>
  <div>
    <!-- Trigger Button (appears as "Connected" status in header) -->
    <button
      @click="openModal"
      class="inline-flex items-center px-4 py-2 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors border border-green-200"
      title="Click to view sync status and manage syncs"
    >
      <span class="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
      <span class="text-sm font-medium">Connected</span>
      <span class="ml-2 text-xs opacity-75">(Admin)</span>
    </button>

    <!-- Modal Overlay -->
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4"
      @click="closeModal"
    >
      <!-- Modal Content -->
      <div
        class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        @click.stop
      >
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold">Sync Management</h2>
            <p class="text-blue-100 text-sm mt-1">Manage Confluence and ADO document synchronization</p>
          </div>
          <button
            @click="closeModal"
            class="text-white hover:bg-white/20 p-2 rounded-lg transition-colors"
          >
            ✕
          </button>
        </div>

        <!-- Tabs -->
        <div class="bg-gray-100 border-b flex gap-4 px-6 py-3">
          <button
            @click="selectedTab = 'summary'"
            :class="[
              'pb-3 px-2 font-medium transition-colors',
              selectedTab === 'summary'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Summary
          </button>
          <button
            @click="selectedTab = 'confluence'"
            :class="[
              'pb-3 px-2 font-medium transition-colors',
              selectedTab === 'confluence'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Confluence
          </button>
          <button
            @click="selectedTab = 'ado'"
            :class="[
              'pb-3 px-2 font-medium transition-colors',
              selectedTab === 'ado'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Azure DevOps
          </button>
          <button
            @click="selectedTab = 'history'"
            :class="[
              'pb-3 px-2 font-medium transition-colors',
              selectedTab === 'history'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            History
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <!-- Loading State -->
          <div v-if="isLoading" class="flex items-center justify-center h-64">
            <div class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p class="text-gray-600">Loading sync data...</p>
              <p class="text-xs text-gray-500 mt-1">This may take a few seconds</p>
            </div>
          </div>

          <!-- Summary Tab -->
          <div v-else-if="selectedTab === 'summary'" class="space-y-6">
            <!-- Sync Controls -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 class="font-bold text-blue-900 mb-4">Trigger Manual Sync</h3>
              <div class="space-y-4">
                <!-- Target Selection -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Sync Target</label>
                  <div class="flex gap-4">
                    <label class="flex items-center">
                      <input
                        v-model="syncTarget"
                        type="radio"
                        value="CONFLUENCE"
                        class="mr-2"
                      />
                      <span class="text-sm">Confluence</span>
                    </label>
                    <label class="flex items-center">
                      <input
                        v-model="syncTarget"
                        type="radio"
                        value="ADO"
                        class="mr-2"
                      />
                      <span class="text-sm">Azure DevOps</span>
                    </label>
                  </div>
                </div>

                <!-- Sync Type -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Sync Type</label>
                  <div class="flex gap-4">
                    <label class="flex items-center">
                      <input
                        v-model="syncType"
                        type="radio"
                        value="delta"
                        class="mr-2"
                      />
                      <span class="text-sm">Recent Changes (Delta)</span>
                    </label>
                  </div>
                </div>

                <!-- Duration -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Look-back Duration: <span class="text-blue-600 font-bold">{{ durationDisplay }}</span>
                  </label>
                  <input
                    v-model.number="duration"
                    type="range"
                    min="1"
                    max="1440"
                    class="w-full"
                    :disabled="isSyncing"
                  />
                  <div class="text-xs text-gray-500 mt-2">
                    Sync documents modified in the last {{ duration }} minute{{ duration !== 1 ? 's' : '' }}
                    <span v-if="duration >= 60" class="ml-2 text-blue-600">
                      (approximately {{ (duration / 24).toFixed(1) }} days)
                    </span>
                  </div>
                </div>

                <!-- Error Message -->
                <div v-if="lastError" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start gap-2">
                  <span class="text-lg mt-0.5">⚠️</span>
                  <div>
                    <p class="font-medium">Sync Error</p>
                    <p class="text-sm mt-1">{{ lastError }}</p>
                  </div>
                </div>

                <!-- Sync Button -->
                <button
                  @click="triggerSync"
                  :disabled="isSyncing"
                  class="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-sm"
                >
                  <span v-if="isSyncing" class="inline-block animate-spin">⟳</span>
                  <span v-if="!isSyncing" class="text-lg">▶</span>
                  {{ isSyncing ? `Syncing ${syncTarget}...` : `Start ${syncTarget} Sync` }}
                </button>
              </div>
            </div>

            <!-- Status Cards -->
            <div v-if="summary" class="grid grid-cols-2 gap-4">
              <!-- Confluence Card -->
              <div class="border rounded-lg p-4 bg-gradient-to-br from-orange-50 to-red-50">
                <h4 class="font-bold text-gray-900 mb-3">📄 Confluence</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between items-center">
                    <span class="text-gray-600">Status:</span>
                    <span :class="statusBadgeClass(summary.confluence.status)">
                      <span>{{ getStatusIcon(summary.confluence.status) }}</span>
                      <span>{{ summary.confluence.status }}</span>
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Last Synced:</span>
                    <span class="font-mono text-xs">{{ formatLocalTime(summary.confluence.last_synced) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Total Syncs:</span>
                    <span class="font-medium">{{ summary.confluence.total_syncs }}</span>
                  </div>
                </div>
              </div>

              <!-- ADO Card -->
              <div class="border rounded-lg p-4 bg-gradient-to-br from-blue-50 to-indigo-50">
                <h4 class="font-bold text-gray-900 mb-3">🎯 Azure DevOps</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between items-center">
                    <span class="text-gray-600">Status:</span>
                    <span :class="statusBadgeClass(summary.ado.status)">
                      <span>{{ getStatusIcon(summary.ado.status) }}</span>
                      <span>{{ summary.ado.status }}</span>
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Last Synced:</span>
                    <span class="font-mono text-xs">{{ formatLocalTime(summary.ado.last_synced) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Total Syncs:</span>
                    <span class="font-medium">{{ summary.ado.total_syncs }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="!summary" class="text-center py-8 text-gray-500">
              <p class="text-sm">📊 No sync data available yet</p>
              <p class="text-xs mt-1">Trigger your first sync to see status information</p>
            </div>

            <!-- Auto-refresh error indicator -->
            <div v-if="refreshError && refreshAttempts >= 2" class="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-xs flex items-center gap-2">
              <span>⚠️</span>
              <span>Auto-refresh encountered an error. Data may be outdated. <button @click="loadSyncData" class="underline font-medium">Retry</button></span>
            </div>
          </div>

          <!-- Confluence Tab -->
          <div v-else-if="selectedTab === 'confluence'" class="space-y-4">
            <div v-if="confluenceLastSync" class="bg-gray-50 rounded-lg p-4">
              <h3 class="font-bold text-gray-900 mb-4">📄 Confluence Last Sync Details</h3>
              <div class="space-y-3 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600">Last Synced:</span>
                  <span class="font-mono text-xs">{{ formatLocalTime(confluenceLastSync.last_completed_at) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Last Document:</span>
                  <span class="font-mono text-xs">{{ confluenceLastSync.last_document || '-' }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-600">Status:</span>
                  <span :class="statusBadgeClass(confluenceLastSync.last_status)">
                    <span>{{ getStatusIcon(confluenceLastSync.last_status) }}</span>
                    <span>{{ confluenceLastSync.last_status }}</span>
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Total Syncs:</span>
                  <span class="font-medium">{{ confluenceLastSync.total_syncs }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">✓ Successful:</span>
                  <span class="font-medium text-green-600">{{ confluenceLastSync.successful_syncs }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">✗ Failed:</span>
                  <span class="font-medium text-red-600">{{ confluenceLastSync.failed_syncs }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <p class="text-sm">📄 No Confluence sync data yet</p>
              <p class="text-xs mt-1">Trigger a Confluence sync from the Summary tab</p>
            </div>
          </div>

          <!-- ADO Tab -->
          <div v-else-if="selectedTab === 'ado'" class="space-y-4">
            <div v-if="adoLastSync" class="bg-gray-50 rounded-lg p-4">
              <h3 class="font-bold text-gray-900 mb-4">🎯 Azure DevOps Last Sync Details</h3>
              <div class="space-y-3 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600">Last Synced:</span>
                  <span class="font-mono text-xs">{{ formatLocalTime(adoLastSync.last_completed_at) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Last Document:</span>
                  <span class="font-mono text-xs">{{ adoLastSync.last_document || '-' }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-600">Status:</span>
                  <span :class="statusBadgeClass(adoLastSync.last_status)">
                    <span>{{ getStatusIcon(adoLastSync.last_status) }}</span>
                    <span>{{ adoLastSync.last_status }}</span>
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Total Syncs:</span>
                  <span class="font-medium">{{ adoLastSync.total_syncs }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">✓ Successful:</span>
                  <span class="font-medium text-green-600">{{ adoLastSync.successful_syncs }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">✗ Failed:</span>
                  <span class="font-medium text-red-600">{{ adoLastSync.failed_syncs }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <p class="text-sm">🎯 No Azure DevOps sync data yet</p>
              <p class="text-xs mt-1">Trigger an ADO sync from the Summary tab</p>
            </div>
          </div>

          <!-- History Tab -->
          <div v-else-if="selectedTab === 'history'" class="space-y-4">
            <h3 class="font-bold text-gray-900">📜 Recent Sync Operations</h3>
            <div v-if="syncHistory.length === 0" class="text-center py-8 text-gray-500">
              <p class="text-sm">📭 No sync history yet</p>
              <p class="text-xs mt-1">Syncs will appear here as they're completed</p>
            </div>
            <div v-else class="space-y-3 overflow-x-auto max-h-96">
              <div
                v-for="sync in syncHistory"
                :key="`${sync.started_at}-${sync.document_id}`"
                :class="['border rounded-lg p-3 text-sm bg-gray-50 hover:bg-gray-100 transition-colors', sync.status === 'ERROR' ? 'border-red-300' : 'border-gray-200']"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="flex gap-2 items-center">
                    <span :class="statusBadgeClass(sync.status)">
                      <span>{{ getStatusIcon(sync.status) }}</span>
                      <span>{{ sync.status }}</span>
                    </span>
                    <span class="text-gray-600">{{ sync.source_system }}</span>
                    <span class="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">{{ sync.sync_type }}</span>
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="text-xs text-gray-600 flex justify-between">
                    <span class="font-mono">{{ sync.document_id }}</span>
                    <span>{{ formatLocalTime(sync.started_at) }}</span>
                  </div>
                  <div class="text-xs text-gray-500 flex justify-between">
                    <span>📊 {{ sync.chunk_count }} chunks, {{ sync.vector_count }} vectors</span>
                    <span v-if="sync.duration_seconds">⏱️ {{ formatDuration(sync.duration_seconds) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-100 border-t p-4 flex justify-between items-center">
          <p class="text-xs text-gray-600">Last updated: {{ new Date().toLocaleTimeString() }}</p>
          <button
            @click="closeModal"
            class="px-4 py-2 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth transitions */
:deep(*) {
  transition: all 0.2s ease;
}

/* Scrollbar styling */
:deep(::-webkit-scrollbar) {
  width: 8px;
}

:deep(::-webkit-scrollbar-track) {
  background: #f1f5f9;
}

:deep(::-webkit-scrollbar-thumb) {
  background: #cbd5e1;
  border-radius: 4px;
}

:deep(::-webkit-scrollbar-thumb:hover) {
  background: #94a3b8;
}
</style>
