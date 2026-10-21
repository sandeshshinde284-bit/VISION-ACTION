<!-- /frontend/src/components/example-integration/NavbarExample.vue -->
<!-- EXAMPLE: How to integrate SyncManagementModal into your navbar -->

<script setup lang="ts">
import { ref } from 'vue'
import SyncManagementModal from '@/components/3-organisms/SyncManagementModal.vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isMenuOpen = ref(false)

// Simulated user data
const currentUser = ref({
  name: 'Sandesh',
  role: 'ADMIN'
})
</script>

<template>
  <!-- Main Navigation Bar -->
  <nav class="bg-white shadow-md sticky top-0 z-30">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo & Brand -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-lg">V</span>
          </div>
          <h1 class="text-xl font-bold text-gray-900">V.I.S.I.O.N.</h1>
        </div>

        <!-- Center Navigation -->
        <div class="hidden md:flex gap-8">
          <router-link
            to="/"
            class="text-gray-600 hover:text-blue-600 transition-colors"
          >
            Home
          </router-link>
          <router-link
            to="/about"
            class="text-gray-600 hover:text-blue-600 transition-colors"
          >
            About
          </router-link>
        </div>

        <!-- Right Side: Sync Manager + User Menu -->
        <div class="flex items-center gap-6">
          <!-- SYNC MANAGEMENT MODAL - Primary Feature -->
          <!-- Shows as "Connected (Admin)" button in navbar -->
          <SyncManagementModal />

          <!-- User Menu -->
          <div class="relative">
            <button
              @click="isMenuOpen = !isMenuOpen"
              class="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                {{ currentUser.name.charAt(0) }}
              </div>
              <span class="hidden sm:inline text-sm font-medium">{{ currentUser.name }}</span>
              <span class="text-gray-400">▼</span>
            </button>

            <!-- Dropdown Menu -->
            <div
              v-if="isMenuOpen"
              class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200"
            >
              <div class="p-4 border-b">
                <p class="text-sm font-medium text-gray-900">{{ currentUser.name }}</p>
                <p class="text-xs text-gray-500">{{ currentUser.role }}</p>
              </div>
              <button
                class="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Profile
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Settings
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors border-t"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Page Content -->
  <main class="max-w-7xl mx-auto px-4 py-8">
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
      <h2 class="text-2xl font-bold text-blue-900 mb-2">Welcome to V.I.S.I.O.N.</h2>
      <p class="text-blue-800">
        Click the <strong>"Connected (Admin)"</strong> button in the navbar above to manage Confluence and Azure DevOps syncs.
      </p>
    </div>

    <!-- Example Content Sections -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Feature Card 1 -->
      <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
        <h3 class="text-lg font-bold text-gray-900 mb-2">Confluence Sync</h3>
        <p class="text-gray-600 text-sm">
          Automatically index and sync Confluence pages to your knowledge base.
        </p>
        <div class="mt-4 pt-4 border-t">
          <p class="text-xs text-gray-500">
            <span class="inline-block w-2 h-2 bg-green-600 rounded-full mr-2"></span>
            Last synced: 5 minutes ago
          </p>
        </div>
      </div>

      <!-- Feature Card 2 -->
      <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
        <h3 class="text-lg font-bold text-gray-900 mb-2">Azure DevOps Sync</h3>
        <p class="text-gray-600 text-sm">
          Keep your work items and tickets synchronized and searchable.
        </p>
        <div class="mt-4 pt-4 border-t">
          <p class="text-xs text-gray-500">
            <span class="inline-block w-2 h-2 bg-yellow-600 rounded-full mr-2"></span>
            Last synced: 2 hours ago
          </p>
        </div>
      </div>

      <!-- Feature Card 3 -->
      <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
        <h3 class="text-lg font-bold text-gray-900 mb-2">Real-Time Status</h3>
        <p class="text-gray-600 text-sm">
          Monitor sync health and history from the admin dashboard.
        </p>
        <div class="mt-4 pt-4 border-t">
          <p class="text-xs text-gray-500">
            <span class="inline-block w-2 h-2 bg-green-600 rounded-full mr-2"></span>
            System healthy
          </p>
        </div>
      </div>
    </div>

    <!-- Instructions -->
    <div class="mt-12 bg-gray-50 rounded-lg p-8">
      <h3 class="text-xl font-bold text-gray-900 mb-6">Getting Started</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <div class="text-3xl font-bold text-blue-600 mb-3">1</div>
          <h4 class="font-bold text-gray-900 mb-2">Click Connected Button</h4>
          <p class="text-gray-600 text-sm">
            Look for the green "Connected (Admin)" button in the top right of the navbar.
          </p>
        </div>
        <div>
          <div class="text-3xl font-bold text-blue-600 mb-3">2</div>
          <h4 class="font-bold text-gray-900 mb-2">View Status & History</h4>
          <p class="text-gray-600 text-sm">
            See real-time sync status, last sync timestamps, and operation history.
          </p>
        </div>
        <div>
          <div class="text-3xl font-bold text-blue-600 mb-3">3</div>
          <h4 class="font-bold text-gray-900 mb-2">Trigger Manual Sync</h4>
          <p class="text-gray-600 text-sm">
            Select a system, adjust duration, and click "Start Sync" to index documents.
          </p>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* Navbar shadow on scroll */
nav {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Smooth transitions */
:deep(*) {
  transition: all 0.2s ease;
}
</style>
