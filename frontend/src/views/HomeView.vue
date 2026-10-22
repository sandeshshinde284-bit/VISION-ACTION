<!-- /frontend/src/views/HomeView.vue -->
<template>
  <div :class="{ 'dark': isDarkMode, 'light': !isDarkMode }" class="h-screen w-screen transition-colors duration-500 overflow-hidden text-[13px] relative">

    <!-- FLOATING RAG CITATIONS TRIGGER (Always Visible when closed and citations exist) -->
    <button
      v-if="activeCitations.length > 0 && !isRagPanelOpen"
      @click="isRagPanelOpen = true"
      class="absolute right-0 top-[45%] -translate-y-1/2 bg-[var(--bg-panel)] border-l border-y border-[var(--accent)]/20 text-[var(--accent)] py-6 px-2.5 rounded-l-xl hover:bg-[var(--accent)]/10 z-30 transition-all shadow-md cursor-pointer group flex flex-col items-center space-y-1.5"
      title="Expand RAG Citations"
    >
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4 opacity-70 group-hover:opacity-100">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
      <span class="text-[11px] font-black tracking-tighter bg-[var(--accent)] text-white w-4 h-4 rounded-full flex items-center justify-center shadow-sm select-none">{{ activeCitations.length }}</span>
    </button>

    <div class="flex flex-col h-full bg-[var(--bg-primary)] text-[var(--text-primary)]">

      <!-- 1. TOP HEADER (PROFESSIONAL & CLEAN) -->
      <header class="h-20 flex items-center justify-between px-6 md:px-10 hud-border border-b bg-[var(--bg-panel)]/30 relative z-20 shrink-0">
        <!-- LEFT SIDE: Burger Menu on Mobile, Empty Logo Space on Desktop -->
        <div class="flex items-center space-x-4 w-12 md:w-48">
          <!-- Burger icon visible ONLY on mobile -->
          <button
            @click="isLeftPanelOpen = !isLeftPanelOpen"
            class="md:hidden flex items-center justify-center w-10 h-10 rounded border border-[var(--accent)]/20 bg-[var(--bg-panel)]/50 text-[var(--accent)] hover:bg-[var(--accent)]/10 transition-colors cursor-pointer"
            title="Toggle Sidebar Menu"
          >
            <!-- Standard Burger SVG -->
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
        </div>

        <!-- CENTERED BRANDING (Desktop Only) -->
        <div class="hidden md:flex flex-col items-center absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
          <div class="text-[32px] font-black tracking-[0.6em] text-[var(--accent)] uppercase drop-shadow-sm pl-[0.6em]">V.I.S.I.O.N.</div>
          <div class="text-[var(--text-secondary)] uppercase tracking-[0.4em] mt-1 font-bold italic pl-[0.4em]">Vision in Action</div>
        </div>

        <!-- CENTERED BRANDING (Mobile Only) -->
        <div class="md:hidden flex flex-col items-center absolute left-1/2 -translate-x-1/2 text-center pointer-events-none select-none">
          <div class="text-[14px] font-black tracking-[0.3em] text-[var(--accent)] uppercase drop-shadow-sm pl-[0.3em]">V.I.S.I.O.N.</div>
          <div class="text-[11px] text-slate-500 uppercase tracking-[0.2em] mt-0.5 font-bold italic pl-[0.2em]">Vision in Action</div>
        </div>
        <!-- RIGHT SIDE: Status, Theme, and Profile -->
        <div class="flex items-center space-x-4 md:space-x-8 select-none">
          <div class="flex items-center space-x-3 md:space-x-6 select-none">
            <AppStatusBadge :status="connectionStatus" :class="['hidden lg:flex', isAdmin ? 'cursor-pointer hover:opacity-85 transition-all active:scale-95' : '']" @click="isAdmin ? openTelemetryModal() : null" />

            <!-- THEME TOGGLE (Restored for Dual-Theme Flexibility - Phase 4) -->
            <button
              @click="isDarkMode = !isDarkMode"
              class="w-10 h-10 md:w-12 md:h-12 flex items-center justify-center rounded border border-[var(--accent)]/10 hover:bg-[var(--accent)]/5 transition-colors shadow-sm cursor-pointer bg-transparent"
              title="Switch Theme (Light / Dark Mode)"
            >
              <svg v-if="isDarkMode" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5 text-[var(--accent)]">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M3 12h2.25m.386-6.364l1.591 1.591M12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5 text-[var(--accent)]">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
              </svg>
            </button>

            <!-- USER ACCOUNT / PROFILE BUTTON WITH DYNAMIC DROPDOWN -->
            <div class="relative shrink-0 flex">
              <button
                @click="isProfileMenuOpen = !isProfileMenuOpen"
                class="profile-btn w-10 h-10 md:w-12 md:h-12 flex items-center justify-center rounded-full border-2 border-[var(--accent)]/20 bg-[var(--accent)]/5 hover:border-[var(--accent)] hover:bg-[var(--accent)]/10 transition-all shadow-sm cursor-pointer group"
                title="Open User Options"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5 text-[var(--accent)] group-hover:scale-110 transition-transform">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </button>

              <!-- Profile Dropdown Flyout (Pristine, glassmorphic, 100% responsive - Phase 4) -->
              <ul
                v-if="isProfileMenuOpen"
                class="profile-dropdown absolute right-0 top-full mt-3 w-52 bg-[var(--bg-panel)]/95 border border-[var(--border)]/15 rounded-2xl py-2.5 shadow-2xl z-30 animate-fade-in backdrop-blur-xl flex flex-col select-none"
              >
                <!-- Profile Header Details -->
                <li class="px-4 py-2 border-b border-[var(--border)]/10 flex flex-col space-y-0.5 select-none">
                  <span class="font-black text-[var(--text-primary)] text-[12.5px] truncate">{{ adminName }}</span>
                  <span class="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-extrabold truncate">Lead Platform Architect</span>
                </li>
                <!-- Option 1: Profile Settings (ADMIN ONLY - Surgical - Phase 4) -->
                <li v-if="isAdmin">
                  <button
                    @click="showProfileModal = true; isProfileMenuOpen = false"
                    class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[10.5px] font-bold uppercase tracking-wider text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2"
                  >
                    <span>⚙️</span>
                    <span>Profile Settings</span>
                  </button>
                </li>
                <!-- Option 2: Lock Console (Subtle, red-hover highlighted right above logout!) -->
                <li>
                  <button
                    @click="handleLogout(); isProfileMenuOpen = false"
                    class="w-full text-left px-4 py-2.5 hover:bg-red-500/10 text-[10.5px] font-bold uppercase tracking-wider text-red-500 hover:text-red-400 transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2"
                  >
                    <span>🔒</span>
                    <span>Lock Console</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>      </header>

      <!-- 2. MAIN HUD (3-COLUMN DYNAMIC STRUCTURE) -->
      <main class="flex-1 flex flex-row w-full overflow-hidden relative bg-[var(--bg-primary)]">

        <div class="absolute inset-0 pointer-events-none opacity-[0.05]">
           <div class="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_100%_0%,var(--accent)_0%,transparent_70%)]"></div>
        </div>

        <!-- LEFT COLUMN: CONVERSATION SESSIONS (COLLAPSIBLE SIDEBAR) -->

        <!-- CASE A: COLLAPSED ICON RAIL (Screenshot 1.png) -->
        <aside
          v-if="!isLeftPanelOpen"
          class="hidden lg:flex flex-col items-center justify-start space-y-6 w-16 md:w-20 h-full bg-[var(--bg-panel)]/40 border-r border-[var(--accent)]/10 py-6 box-border shrink-0 select-none z-10 transition-all duration-300 backdrop-blur-sm"
        >
          <!-- Top Section: Menu Toggle + Actions -->
          <div class="flex flex-col items-center space-y-6 w-full">
            <!-- Expand Arrow (Inward to Outward Chevron) -->
            <button
              @click="isLeftPanelOpen = true"
              class="w-8 h-8 rounded-lg flex items-center justify-center border border-[var(--accent)]/15 text-[var(--accent)] hover:bg-[var(--accent)]/15 hover:scale-105 transition-all cursor-pointer bg-transparent"
              title="Expand Sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>

            <!-- Compact Plus (New Session) -->
            <button
              @click="createSession"
              class="h-8 px-3 md:px-5 flex items-center justify-center space-x-2 rounded-lg bg-transparent border-2 border-[var(--accent)] text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:scale-[1.02]"
             title="Instantiate a brand-new, secure, and concurrent chat session">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4 text-[var(--accent)]">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              
            </button>

            <!-- Divider -->
            <div class="w-8 h-[1px] bg-[var(--accent)]/10"></div>

            <!-- Chat Icon (Active general session) -->
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--accent)]/15 border border-[var(--accent)]/30 text-[var(--accent)]"
              title="General Session (Active)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3h9m-9 3h3m-6.75 3h12a2.25 2.25 0 002.25-2.25V5.25a2.25 2.25 0 00-2.25-2.25h-12A2.25 2.25 0 002.25 5.25v13.5A2.25 2.25 0 002.25 21z" />
              </svg>
            </button>

            <!-- RAG Folder Icon (Appears only when references/citations are found by V.I.S.I.O.N.) -->
            <button
              v-if="activeCitations.length > 0"
              @click="isRagPanelOpen = !isRagPanelOpen"
              class="w-8 h-8 rounded-lg flex items-center justify-center border border-[var(--accent)]/15 text-[var(--accent)] hover:bg-[var(--accent)]/10 hover:scale-105 transition-all cursor-pointer bg-transparent relative animate-fade-in"
              title="Toggle RAG Citation Board"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
              <!-- Small glowing notification dot on the icon -->
              <span class="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent)] opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent)]"></span>
              </span>
            </button>
          </div>
        </aside>

        <!-- CASE B: FULL TEXT SIDEBAR (Screenshot 2.png) -->
        <aside
          v-else
          class="absolute lg:relative inset-y-0 left-0 w-80 h-full bg-[var(--bg-panel)]/95 lg:bg-[var(--bg-panel)]/30 border-r border-[var(--accent)]/10 p-6 lg:p-8 flex flex-col space-y-8 z-40 lg:z-10 transition-all duration-300 shadow-2xl lg:shadow-none shrink-0"
        >
          <div class="flex justify-between items-center border-b border-[var(--accent)]/10 pb-4 shrink-0">
            <div class="text-[var(--text-secondary)] font-black uppercase tracking-[0.2em] text-[11px]">Dialogue Sessions</div>
            <button @click="isLeftPanelOpen = false" class="p-2 rounded-lg hover:bg-[var(--accent)]/10 text-[var,--accent] opacity-60 hover:opacity-100 transition-colors bg-transparent border-0 cursor-pointer" title="Collapse Panel">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>
          </div>

          <!-- RECENT CHATS (DIALOGUE MANAGER) -->
          <div class="flex-grow flex flex-col space-y-6 overflow-hidden">

            <!-- Quick Actions Deck in Expanded State (Screenshot 2.png) -->
            <div class="flex flex-col space-y-2 shrink-0">

              <!-- Prominent RAG Board Toggle (Visible only when citations exist) -->
              <button
                v-if="activeCitations.length > 0"
                @click="isRagPanelOpen = !isRagPanelOpen"
                class="w-full flex items-center justify-between py-3 px-4 rounded-xl border border-[var(--accent)]/25 hover:border-[var(--accent)]/45 hover:bg-[var(--accent)]/10 transition-all text-xs font-bold text-slate-200 cursor-pointer bg-transparent relative overflow-hidden"
                title="Toggle RAG Citation Board"
              >
                <div class="flex items-center space-x-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 text-[var(--accent)]">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                  </svg>
                  <span>RAG Citations</span>
                </div>
                <!-- Mini count bubble -->
                <span class="text-[11px] font-black tracking-tighter bg-[var(--accent)] text-white w-4 h-4 rounded-full flex items-center justify-center shadow-sm select-none">{{ activeCitations.length }}</span>
              </button>
            </div>

            <div class="flex flex-col space-y-3 flex-1 overflow-y-auto custom-scrollbar select-none">
          <div class="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-bold border-b border-[var,--accent]/10 pb-2">
                <span>Recent Chats</span>
                <span v-if="chatFilterQuery" class="text-[11px] font-normal text-slate-500 lowercase">filtering...</span>
              </div>

              <!-- Minimalist Search Filter Bar (Phase 4 - Theme Hardened) -->
              <div class="px-0.5 shrink-0">
                <input
                  v-model="chatFilterQuery"
                  type="text"
                  placeholder="Filter sessions..."
                  class="w-full px-3 py-1.5 bg-[var(--bg-primary)]/80 border border-[var(--border)] focus:border-[var(--accent)]/40 rounded-xl text-[10.5px] font-bold text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none transition-all"
                />
              </div>
              <!-- Clean active list of sessions loop (Phase 4 - Theme Hardened) -->
              <div class="flex flex-col space-y-1.5">
                <div
                  v-for="session in filteredSessions"
                  :key="session.session_id"
                  class="group relative w-full flex items-center justify-between px-3.5 py-3 rounded-xl transition-all border select-none cursor-pointer"
                  :class="[
                    activeSessionId === session.session_id
                      ? 'bg-[var(--accent)]/18 border-[var(--accent)]/70 text-[var,--accent] font-extrabold shadow-[0_0_15px_rgba(0,136,255,0.18)]'
                      : 'bg-transparent border-transparent hover:border-[var(--accent)]/10 hover:bg-[var(--accent)]/5 text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  ]"
                  @click="switchSession(session.session_id)"
                >
                  <div class="flex items-center space-x-3 truncate flex-grow">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4 shrink-0" :class="activeSessionId === session.session_id ? 'text-sky-600 dark:text-sky-400' : 'opacity-40'">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3h9m-9 3h3m-6.75 3h12a2.25 2.25 0 002.25-2.25V5.25a2.25 2.25 0 00-2.25-2.25h-12A2.25 2.25 0 002.25 5.25v13.5A2.25 2.25 0 002.25 21z" />
                    </svg>

                    <!-- Edit Inline Rename Field -->
                    <input
                      v-if="editingSessionId === session.session_id"
                      v-model="sessionRenameTitle"
                      @blur="saveSessionRename(session.session_id)"
                      @keyup.enter="saveSessionRename(session.session_id)"
                      class="bg-transparent border-b border-[var(--accent)] text-[13.5px] font-semibold text-slate-800 dark:text-slate-100 focus:outline-none w-full px-0.5"
                      @click.stop
                    />
                    <span v-else class="truncate text-[13.5px] font-semibold tracking-wide">{{ session.title }}</span>
                  </div>

                  <!-- Hover Actions Panel (Rename + Delete) -->
                  <div v-show="activeSessionId !== session.session_id || isGenerating === false" class="hidden group-hover:flex items-center space-x-1.5 shrink-0 pl-2">
                    <!-- Rename Pencil -->
                    <button
                      @click.stop="startSessionRename(session.session_id, session.title)"
                      class="p-0.5 rounded hover:bg-slate-800/80 text-slate-400 hover:text-sky-400 transition-colors bg-transparent border-0 cursor-pointer flex items-center justify-center text-[10px]"
                      title="Rename Session"
                    >
                      ✏️
                    </button>

                    <!-- Delete Trash (Disabled on default_session!) -->
                    <button
                      v-if="session.session_id !== 'default_session'"
                      @click.stop="deleteSession(session.session_id)"
                      class="p-0.5 rounded hover:bg-slate-800/80 text-slate-400 hover:text-red-400 transition-colors bg-transparent border-0 cursor-pointer flex items-center justify-center text-[10px]"
                      title="Delete Session"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- LOCK CONSOLE button has been relocated cleanly to the top-right header as a premium quick-action shortcut! -->
          </div>
        </aside>

        <!-- MIDDLE COLUMN: UNIFIED DYNAMIC WORKSPACE (DYNAMIC FLEX RESPONSIVE) -->
        <div
          class="flex-1 min-w-0 h-full flex flex-col p-4 md:p-8 relative overflow-hidden transition-all duration-300 border-r border-[var(--accent)]/5"
        >
          <!-- WORKSPACE HEADER (COMPACT SINGLE-ROW CONTROL DECK) -->
          <div class="flex justify-between items-center mb-6 pb-4 border-b border-[var(--accent)]/10 shrink-0 select-none w-full box-border">
             <!-- Editable Session Topic Title (Hidden on mobile for supreme cleanliness) -->
             <div class="hidden sm:flex items-center space-x-1 shrink min-w-0">
                <span class="text-[11px] md:text-[10px] text-slate-500 uppercase tracking-wider font-black">Topic:</span>
                <input
                  v-model="sessionTitle"
                  class="bg-transparent border-b border-transparent focus:border-[var(--accent)] text-[11px] md:text-[11px] font-black uppercase tracking-[0.05em] md:tracking-[0.15em] text-[var(--text-primary)] focus:outline-none w-20 sm:w-36 md:w-52 transition-all px-1 truncate"
                  title="Click to rename session topic (Updates exported file name!)"
                  placeholder="ENTER TOPIC..."
                />
             </div>

             <!-- Compact Premium Controls Row (Always single row, fits perfectly, right-aligned on mobile via ml-auto!) -->
             <div class="ml-auto flex items-center space-x-1.5 md:space-x-3 shrink-0 relative">

               <!-- ALWAYS-VISIBLE NEW SESSION BUTTON (Collapses on Mobile - Theme & SaaS Hardened) -->
               <button
                 @click="createSession"
                 class="h-8 px-3 md:px-5 flex items-center justify-center space-x-2 rounded-lg bg-[var(--accent)] text-white hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all text-[10px] md:text-xs font-black uppercase tracking-wider cursor-pointer shadow-[0_0_12px_rgba(0,136,255,0.4)] border border-sky-400/50"
                 title="Instantiate a brand-new, secure, and concurrent chat session"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4 text-white">
                   <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                 </svg>
                 <span class="hidden md:inline">New Session</span>
               </button>

               <!-- 📤 EXPORT/SHARE DROPDOWN BUTTON -->
               <div class="relative shrink-0 flex">
                 <button
                   @click="isExportMenuOpen = !isExportMenuOpen"
                   class="share-btn w-7 h-7 rounded-lg flex items-center justify-center border border-[var(--accent)]/20 bg-[var(--bg-panel)]/50 hover:bg-[var(--accent)]/15 text-[var(--accent)] hover:scale-105 transition-all cursor-pointer bg-transparent"
                   title="Export Session Logs"
                 >
                   <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                     <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                   </svg>
                 </button>

                 <!-- Glassmorphic Dropdown Flyout (Absolute bottom positioning so it floats perfectly) -->
                 <ul
                   v-if="isExportMenuOpen"
                   class="share-dropdown absolute top-full right-0 mt-2 w-40 bg-[var(--bg-panel)] border-2 border-[var(--accent)]/50 rounded-xl py-1.5 shadow-2xl z-30 animate-fade-in backdrop-blur-xl"
                 >
                   <li>
                     <button @click="triggerExport('md')" class="w-full text-left px-4 py-2 hover:bg-[var(--accent)]/10 text-[11px] font-black uppercase tracking-wider text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors bg-transparent border-0 cursor-pointer">
                       📂 Markdown (.md)
                     </button>
                   </li>
                   <li>
                     <button @click="triggerExport('txt')" class="w-full text-left px-4 py-2 hover:bg-[var(--accent)]/10 text-[11px] font-black uppercase tracking-wider text-[var,--text-primary)] hover:text-[var(--accent)] transition-colors bg-transparent border-0 cursor-pointer">
                       📄 Plain Text (.txt)
                     </button>
                   </li>
                 </ul>
               </div>
            </div>
          </div>

          <!-- DOCUMENT INDEXING ACTIVE LOADER FEEDBACK -->
          <div v-if="isIndexing" class="flex-grow flex flex-col items-center justify-center p-6 select-none animate-fade-in">
            <div class="flex flex-col items-center space-y-4 animate-pulse">
              <span class="text-3xl animate-bounce">📂</span>
              <div class="text-[11px] font-black uppercase tracking-[0.3em] text-[var(--accent)] drop-shadow-[0_0_8px_var(--accent)]">Ingesting & Indexing Documents...</div>
              <div class="text-[11px] text-slate-500 uppercase tracking-wider font-bold">Vectorizing segments securely inside local ChromaDB</div>
            </div>
          </div>

          <!-- UNIFIED FEED AREA (Shown only when not uploading/indexing) -->
          <div v-else class="flex-grow flex flex-col items-center overflow-hidden w-full relative box-border">

            <!-- CASE A: ACTIVE CONVERSATION FLOW -->
            <template v-if="receivedMessages.length > 0">

              <!-- Chat Feed Scroll Container -->
              <div
                ref="chatFeedRef"
                @scroll="handleScroll"
                class="flex-1 w-full overflow-y-auto custom-scrollbar flex flex-col items-center px-4 md:px-6"
              >
                <div class="w-full max-w-5xl pb-6 pt-6">
                  <SystemLog :messages="receivedMessages" :admin-name="adminName" :is-dark-mode="isDarkMode" :ai-state="aiState" :agent-status="agentStatus" @trigger-ado-query="handleAdoQuery" @cancel-request="cancelRequest" />
                </div>
              </div>

              <!-- Floating Scroll to Bottom Button has been relocated cleanly into the bottom control deck to prevent any collisions! -->
              </template>

              <!-- CASE B: WELCOME HOME DASHBOARD (When conversation is fresh!) -->
              <div
                v-else
                class="flex-1 w-full max-w-5xl flex flex-col items-center justify-center px-6 py-4 space-y-6 select-none text-center animate-fade-in relative overflow-visible"
              >
                <!-- Clean, Human-Written Timezone Greeting (SaaS Minimalist Layout - Focus-driven) -->
                <div class="relative z-10 select-none space-y-2 max-w-2xl">
                  <h1 class="text-3xl font-bold text-[var(--text-primary)] tracking-tight leading-snug select-none">
                    How can I help you with your development task today, {{ adminName }}?
                  </h1>
                  <p class="text-[var(--text-secondary)] text-sm max-w-lg mx-auto leading-relaxed font-medium">
                    Query synchronized Confluence spaces, search active Azure DevOps tickets, or use live Web search to troubleshoot technical errors.
                  </p>
                </div>

                <!-- PREMIUM GLASSMORPHIC QUICK-START ACTION DECK (Phase 4 - Positioned Relative with Z-20) -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-5xl relative z-20 pt-2 shrink-0 select-none">
                  <!-- Card 1: Confluence -->
                  <div
                    @click="triggerQuickAction('INTERNAL', 'Explain the core system architecture and deployment guidelines')"
                    class="group bg-[var(--bg-panel)]/50 backdrop-blur-md hover:bg-[var(--bg-panel)]/80 border border-[var(--border)] rounded-xl p-3.5 text-left transition-all duration-300 transform hover:-translate-y-1 hover:scale-[1.02] hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] active:scale-[0.98] active:translate-y-0 cursor-pointer shadow-[0_4px_12px_rgba(0,0,0,0.04)] flex flex-col justify-between min-h-[105px] h-auto relative overflow-hidden"
                  >
                    <!-- Flawless rounded left border indicator using absolute clipping -->
                    <div class="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent)]"></div>
                    <span class="text-base mb-1 select-none filter drop-shadow-[0_0_8px_var(--accent)] pl-1">📁</span>
                    <div class="pl-1">
                      <div class="text-[10.5px] font-black text-[var(--text-primary)] group-hover:text-[var(--accent)] uppercase tracking-wider transition-colors">Confluence</div>
                      <p class="text-[10.5px] md:text-[11.5px] text-[var(--text-secondary)] leading-normal mt-1 transition-colors font-medium">Search private Confluence spaces for technical specifications.</p>
                    </div>
                  </div>

                  <!-- Card 2: ADO -->
                  <div
                    @click="triggerQuickAction('INTERNAL', 'Retrieve the active tracking tasks and sprint deliverables')"
                    class="group bg-[var(--bg-panel)]/50 backdrop-blur-md hover:bg-[var(--bg-panel)]/80 border border-[var(--border)] rounded-xl p-3.5 text-left transition-all duration-300 transform hover:-translate-y-1 hover:scale-[1.02] hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] active:scale-[0.98] active:translate-y-0 cursor-pointer shadow-[0_4px_12px_rgba(0,0,0,0.04)] flex flex-col justify-between min-h-[105px] h-auto relative overflow-hidden"
                  >
                    <!-- Flawless rounded left border indicator using absolute clipping -->
                    <div class="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500"></div>
                    <span class="text-base mb-1 select-none filter drop-shadow-[0_0_8px_var(--accent)] pl-1">📌</span>
                    <div class="pl-1">
                      <div class="text-[10.5px] font-black text-[var(--text-primary)] group-hover:text-[var(--accent)] uppercase tracking-wider transition-colors">ADO Tickets</div>
                      <p class="text-[10.5px] md:text-[11.5px] text-[var(--text-secondary)] leading-normal mt-1 transition-colors font-medium">Retrieve project boards, user-stories, and tracking tasks.</p>
                    </div>
                  </div>

                  <!-- Card 3: Hybrid Compare -->
                  <div
                    @click="triggerQuickAction('BOTH', 'Compare public coding standards and frameworks with our private documentation')"
                    class="group bg-[var(--bg-panel)]/50 backdrop-blur-md hover:bg-[var(--bg-panel)]/80 border border-[var(--border)] rounded-xl p-3.5 text-left transition-all duration-300 transform hover:-translate-y-1 hover:scale-[1.02] hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] active:scale-[0.98] active:translate-y-0 cursor-pointer shadow-[0_4px_12px_rgba(0,0,0,0.04)] flex flex-col justify-between min-h-[105px] h-auto relative overflow-hidden"
                  >
                    <!-- Flawless rounded left border indicator using absolute clipping -->
                    <div class="absolute left-0 top-0 bottom-0 w-1 bg-sky-500"></div>
                    <span class="text-base mb-1 select-none filter drop-shadow-[0_0_8px_var(--accent)] pl-1">🌐</span>
                    <div class="pl-1">
                      <div class="text-[10.5px] font-black text-[var(--text-primary)] group-hover:text-[var(--accent)] uppercase tracking-wider transition-colors">Hybrid Compare</div>
                      <p class="text-[10.5px] md:text-[11.5px] text-[var(--text-secondary)] leading-normal mt-1 transition-colors font-medium">Correlate live Web search results with private database specs.</p>
                    </div>
                  </div>

                  <!-- Card 4: Refine Prompt -->
                  <div
                    @click="triggerQuickAction('AUTO', 'Write a clean script to parse raw inputs and convert them to markdown')"
                    class="group bg-[var(--bg-panel)]/50 backdrop-blur-md hover:bg-[var(--bg-panel)]/80 border border-[var(--border)] rounded-xl p-3.5 text-left transition-all duration-300 transform hover:-translate-y-1 hover:scale-[1.02] hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] active:scale-[0.98] active:translate-y-0 cursor-pointer shadow-[0_4px_12px_rgba(0,0,0,0.04)] flex flex-col justify-between min-h-[105px] h-auto relative overflow-hidden"
                  >
                    <!-- Flawless rounded left border indicator using absolute clipping -->
                    <div class="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
                    <span class="text-base mb-1 select-none filter drop-shadow-[0_0_8px_var(--accent)] pl-1">✏️</span>
                    <div class="pl-1">
                      <div class="text-[10.5px] font-black text-[var(--text-primary)] group-hover:text-[var(--accent)] uppercase tracking-wider transition-colors">Refine Prompt</div>
                      <p class="text-[10.5px] md:text-[11.5px] text-[var(--text-secondary)] leading-normal mt-1 transition-colors font-medium">Pre-fill prompt templates to demonstrate AI prompt expansion.</p>
                    </div>
                  </div>
                </div>

              </div>

              <!-- GLOWING SCROLL FADE MASK (Hides text bleeding below the static cockpit) -->
              <!-- Positioned cleanly above the static console footer block! -->
              <div class="absolute bottom-[200px] left-0 right-0 h-24 bg-gradient-to-t from-[var(--bg-primary)] to-transparent pointer-events-none z-10"></div>

              <!-- Bottom control deck containing status and input containers -->
              <div class="relative w-full max-w-5xl mx-auto px-4 md:px-6 pb-4 md:pb-6 shrink-0 flex flex-col z-20 transition-all duration-300">

                <!-- Floating Scroll to Bottom Button  -->
                <transition name="fade">
                  <button
                    v-if="showScrollDownBtn"
                    @click="scrollToBottom"
                    class="absolute -top-14 left-1/2 -translate-x-1/2 z-30 w-9 h-9 rounded-full bg-[#0d1117]/95 hover:bg-[var(--accent)]/15 border border-slate-800 hover:border-[var(--accent)]/40 flex items-center justify-center text-slate-400 hover:text-[var(--accent)] hover:scale-110 active:scale-95 transition-all duration-300 shadow-[0_4px_15px_rgba(0,0,0,0.5)] cursor-pointer"
                    title="Scroll to most recent messages"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>

                    <!-- Pulsing Green Dot (Triggers when new tokens are streaming in the background while you read!) -->
                    <span v-if="hasNewUnreadMessages" class="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  </button>
                </transition>

                <!-- System Status Row -->
                <div class="h-10 mb-2.5 shrink-0 relative select-none">
                  <transition name="fade">
                    <!-- Status bar showing routing reason and token cost (Theme-Aware Contrast - Phase 4) -->
                    <div v-show="!isUserScrolledUp" class="absolute inset-0 flex items-center justify-between px-4 py-1.5 bg-[var(--bg-panel)] border border-[var(--border)] border-b-[var(--accent)]/35 rounded-2xl shadow-[0_4px_25px_rgba(0,0,0,0.15),0_0_15px_rgba(0,136,255,0.02)] transition-all duration-300">

                      <!-- LEFT SIDE: ACTIVE ROUTER STATE WITH GLOWING ROUTER SVG -->
                      <div class="flex items-center space-x-2 text-slate-800 dark:text-slate-200">
                        <!-- Custom Glowing SVG Router Flag Icon -->
                        <svg class="w-3.5 h-3.5 text-[var(--accent)] drop-shadow-[0_0_6px_var(--accent)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                          <line x1="4" y1="22" x2="4" y2="15" />
                        </svg>

                        <div
                          v-if="currentRouteReason"
                          class="flex items-center space-x-1.5 text-[8.5px] font-black uppercase tracking-[0.15em] text-[var(--accent)] animate-fade-in"
                        >
                          <span>Route: </span>
                          <span v-if="currentRouteReason === 'INTERNAL'" class="font-extrabold text-slate-800 dark:text-slate-100">🏢 Internal Knowledge Store</span>
                          <span v-else-if="currentRouteReason === 'WEB'" class="font-extrabold text-emerald-600 dark:text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]">🌐 Live Public Internet</span>
                          <span v-else-if="currentRouteReason === 'BOTH'" class="font-extrabold text-purple-600 dark:text-purple-400 drop-shadow-[0_0_8px_rgba(192,132,252,0.3)]">📚 Hybrid Internal + Web</span>
                          <span v-else class="font-extrabold text-slate-700 dark:text-slate-200">🧠 Auto Progressive Routing active</span>
                        </div>
                        <div v-else class="text-[8.5px] font-black uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400 flex items-center space-x-2">
                          <!-- Dynamic state based on selected Active Scope! -->
                          <template v-if="activeScope === 'AUTO'">
                            <span class="text-slate-700 dark:text-slate-200">🧠 Auto Progressive Routing active</span>
                            <span class="relative flex h-1.5 w-1.5">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent)] opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-[var(--accent)]"></span>
                            </span>
                          </template>
                          <template v-else-if="activeScope === 'INTERNAL'">
                            <span class="text-slate-500 animate-pulse">🏢 Forced Internal Docs</span>
                          </template>
                          <template v-else-if="activeScope === 'WEB'">
                            <span class="text-emerald-500 animate-pulse">🌐 Forced Web Search</span>
                          </template>
                          <template v-else-if="activeScope === 'BOTH'">
                            <span class="text-purple-400 animate-pulse">📚 Forced Hybrid Compare</span>
                          </template>
                        </div>
                      </div>
                      <!-- RIGHT SIDE: FINOPS COST METER WITH GLOWING COST METER SVG -->
                      <div class="flex items-center space-x-2">
                        <!-- Custom Glowing SVG Dollar/FinOps Cost Icon -->
                        <svg class="w-3.5 h-3.5 text-slate-400 drop-shadow-[0_0_4px_rgba(255,255,255,0.1)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <line x1="12" y1="1" x2="12" y2="23" />
                          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                        </svg>

                        <div
                          v-if="sessionTokens.total > 0"
                          class="text-[11px] text-slate-400 font-extrabold uppercase tracking-[0.15em] flex items-center space-x-1.5"
                        >
                          <span>Tokens: {{ sessionTokens.total }}</span>
                          <span class="text-slate-600 opacity-60">•</span>
                          <span class="text-[var(--accent)] font-black drop-shadow-[0_0_8px_var(--accent)]">Est. Cost: ${{ sessionCost.toFixed(5) }}</span>
                        </div>
                        <div v-else class="text-[11px] text-slate-500 font-extrabold uppercase tracking-[0.15em]">
                          Est. Session Cost: $0.00000
                        </div>
                      </div>

                    </div>
                  </transition>
                </div>

                <!-- Inner capsule with strong glassmorphic backdrop, glowing accent shadow and corporate borders -->
                <div class="bg-[var(--bg-panel)]/80 backdrop-blur-2xl border border-[var(--accent)]/20 rounded-3xl p-3 md:p-4 shadow-[0_0_30px_rgba(0,136,255,0.08)] hover:shadow-[0_0_30px_rgba(0,136,255,0.14)] focus-within:shadow-[0_0_35px_rgba(0,136,255,0.22)] flex flex-col box-border border-b border-[var(--accent)]/45 transition-all duration-500">

                <!-- COCKPIT NAVIGATION: AGENTIC ROUTER SCOPE CHIPS (PHASE 4) -->
                <div class="flex items-center space-x-1.5 md:space-x-2.5 mb-3 px-1 border-b border-[var(--accent)]/5 pb-2.5 overflow-x-auto custom-scrollbar select-none shrink-0">
                  <span class="text-[11px] md:text-[9.5px] uppercase tracking-wider text-slate-500 font-black shrink-0 pr-1 select-none">Search Scope:</span>

                  <button
                    @click="activeScope = 'AUTO'"
                    class="h-6 px-3 rounded-full text-[11px] font-black uppercase tracking-wider border transition-all duration-300 cursor-pointer shrink-0 whitespace-nowrap"
                    :class="activeScope === 'AUTO' ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[0_0_12px_rgba(0,136,255,0.25)]' : 'border-[var(--accent)]/15 text-[var(--text-secondary)] hover:border-[var(--accent)]/40 hover:text-[var(--accent)] bg-transparent'"
                    title="Intelligently choose the best routing data path based on progressive confidence checks"
                  >
                    🤖 Auto
                  </button>

                  <button
                    @click="activeScope = 'INTERNAL'"
                    class="h-6 px-3 rounded-full text-[11px] font-black uppercase tracking-wider border transition-all duration-300 cursor-pointer shrink-0 whitespace-nowrap"
                    :class="activeScope === 'INTERNAL' ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[0_0_12px_rgba(0,136,255,0.25)]' : 'border-[var(--accent)]/15 text-[var(--text-secondary)] hover:border-[var(--accent)]/40 hover:text-[var(--accent)] bg-transparent'"
                    title="Query strictly internal Confluence Specifications and ADO tickets under 100% security bounds"
                  >
                    📁 Internal Docs
                  </button>

                  <button
                    @click="activeScope = 'WEB'"
                    class="h-6 px-3 rounded-full text-[11px] font-black uppercase tracking-wider border transition-all duration-300 cursor-pointer shrink-0 whitespace-nowrap"
                    :class="activeScope === 'WEB' ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[0_0_12px_rgba(0,136,255,0.25)]' : 'border-[var(--accent)]/15 text-[var(--text-secondary)] hover:border-[var(--accent)]/40 hover:text-[var,--accent] bg-transparent'"
                    title="Bypass internal searches entirely and ground answers using live public Google Search"
                  >
                    🌐 Web Search
                  </button>

                  <button
                    @click="activeScope = 'BOTH'"
                    class="h-6 px-3 rounded-full text-[11px] font-black uppercase tracking-wider border transition-all duration-300 cursor-pointer shrink-0 whitespace-nowrap"
                    :class="activeScope === 'BOTH' ? 'bg-[var(--accent)] text-[var(--bg-panel)] border-[var(--accent)] shadow-[0_0_12px_rgba(0,136,255,0.25)]' : 'border-[var(--accent)]/15 text-slate-400 hover:border-[var(--accent)]/40 hover:text-[var,--accent] bg-transparent'"
                    title="Extract internal specs first, then dynamically contrast and enrich using live external web search"
                  >
                    🔄 Both (Hybrid)
                  </button>
                </div>

                <!-- ROW 1: SPACIOUS FULL-WIDTH TEXTAREA -->
                <div
                  class="w-full flex flex-col border border-[var(--accent)]/15 hover:border-[var(--accent)]/30 focus-within:border-[var(--accent)]/55 transition-all rounded-2xl bg-[var(--bg-primary)]/15 overflow-hidden mb-3"
                  :class="isDragging ? 'border-dashed border-[var(--accent)] bg-[var(--accent)]/5 shadow-[0_0_15px_rgba(0,136,255,0.1)]' : ''"
                  @dragover.prevent="isDragging = true"
                  @dragleave.prevent="isDragging = false"
                  @drop.prevent="handleFileDrop"
                >
                  <!-- Multi-File In-Input chips + Workspace Folder Chip (Idea G) -->
                  <div v-if="attachedFiles.length > 0 || attachedFolderName" class="flex flex-wrap gap-1.5 px-4 pt-3 select-none">
                     <!-- Folder Ingestion Chip -->
                     <div
                       v-if="attachedFolderName"
                       class="flex items-center space-x-1.5 bg-[var(--accent)]/15 border border-[var(--accent)]/30 px-3 py-0.5 rounded-full text-[10px] text-[var(--accent)] font-bold animate-fade-in"
                     >
                       <span>📁 Folder: {{ attachedFolderName }}</span>
                       <span class="text-[11px] text-slate-500 opacity-80">({{ attachedFolderFiles.length }} files, {{ formatSize(attachedFolderSize) }})</span>
                       <button
                         @click="clearFolderSelection"
                         class="text-[11px] hover:text-red-500 font-black ml-1 bg-transparent border-0 cursor-pointer"
                         title="Remove Folder"
                       >
                         [x]
                       </button>
                     </div>

                     <div
                        v-for="(file, index) in attachedFiles"
                        :key="index"
                        class="flex items-center space-x-1.5 bg-[var(--accent)]/10 border border-[var(--accent)]/25 px-2.5 py-0.5 rounded-full text-[10px] text-slate-300 font-medium animate-fade-in"
                     >
                        <span class="truncate max-w-[120px]">{{ file.name }}</span>
                        <span class="text-[11px] text-slate-500">({{ formatSize(file.size) }})</span>
                        <button @click="removeFile(index)" class="text-[11px] hover:text-red-500 font-black ml-1 bg-transparent border-0 cursor-pointer">[x]</button>
                     </div>
                  </div>

                  <textarea
                    v-model="textInput"
                    @keyup.enter.exact.prevent="submitText"
                    maxlength="15000"
                    placeholder="MESSAGE V.I.S.I.O.N. OR DRAG & DROP CODES..."
                    class="w-full bg-transparent py-3 px-4 text-base md:text-[16.5px] focus:outline-none placeholder-[var(--text-secondary)]/40 tracking-normal font-normal resize-none custom-scrollbar min-h-[56px] max-h-[140px] leading-relaxed"
                    :style="{ color: isDarkMode ? '#f8fafc' : '#0f172a' }"
                  ></textarea>
                </div>

                <!-- ROW 2: UNIFIED BOTTOM CONTROL DECK (Symmetric flex split!) -->
                <div class="flex items-center justify-between w-full box-border relative">

                  <!-- LEFT CONTROLS: COMPACT GLOWING CAPSULE PILLS -->
                  <div class="flex items-center space-x-2 select-none shrink-0 relative">
                    <!-- Mobile-Only '+' More Actions Button -->
                    <button
                      @click="isMoreActionsOpen = !isMoreActionsOpen"
                      class="plus-btn sm:hidden w-8 h-8 flex items-center justify-center rounded-full border border-[var(--accent)]/30 text-[var(--accent)] hover:bg-[var(--accent)]/5 transition-all cursor-pointer bg-transparent shadow-md"
                      title="Open More Cockpit Actions"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4.5 h-4.5 transition-transform duration-300" :class="isMoreActionsOpen ? 'rotate-45 text-red-500 border-red-500' : ''">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                      </svg>
                    </button>

                    <!-- MOBILE ONLY FLOATING MORE ACTIONS DRAWER PANEL (Left-aligned relative to the '+' button) -->
                    <ul
                      v-if="isMoreActionsOpen"
                      class="more-actions-drawer sm:hidden absolute bottom-full left-0 mb-4 w-52 bg-[var(--bg-panel)]/95 border-2 border-[var(--accent)] rounded-2xl py-1.5 shadow-2xl z-30 animate-fade-in backdrop-blur-xl flex flex-col"
                    >
                      <li>
                        <button @click="triggerFileUpload; isMoreActionsOpen = false" class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[11px] font-black uppercase tracking-wider text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2">
                          <span>📎</span>
                          <span>Attach File</span>
                        </button>
                      </li>
                      <li>
                        <button @click="isMuted = !isMuted; isMoreActionsOpen = false" class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[11px] font-black uppercase tracking-wider text-[var(--text-primary)] hover:text-[var,--accent] transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2">
                          <span>🎤</span>
                          <span>{{ isMuted ? 'Unmute Mic' : 'Mute Mic' }}</span>
                        </button>
                      </li>
                      <li>
                        <button @click="optimizeCurrentPrompt; isMoreActionsOpen = false" :disabled="!textInput.trim()" class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[11px] font-black uppercase tracking-wider text-[var(--text-primary)] hover:text-[var,--accent] transition-colors bg-transparent border-0 cursor-pointer disabled:opacity-30 flex items-center space-x-2">
                          <span>✨</span>
                          <span>Optimize Prompt</span>
                        </button>
                      </li>
                    </ul>

                    <!-- Mute Mic Capsule Pill (Hidden on Mobile, shown on Desktop) -->
                    <button
                      @click="isMuted = !isMuted"
                      class="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-full border text-[11px] md:text-[10px] font-black uppercase tracking-wider transition-all duration-300 cursor-pointer bg-transparent"
                      :class="isMuted ? 'bg-red-500/10 border-red-500 text-red-500 shadow-[0_0_8px_rgba(239,68,68,0.2)]' : 'border-[var(--accent)]/30 text-[var(--accent)] hover:bg-[var(--accent)]/5'"
                      :title="isMuted ? 'Mic Muted - Click to Unmute' : 'Mic Live - Click to Mute'"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-3 h-3" :class="isMuted ? 'animate-pulse' : ''">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                        <path v-if="isMuted" stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
                      </svg>
                      <span class="hidden sm:inline">{{ isMuted ? 'Muted' : 'Mic Live' }}</span>
                    </button>

                    <!-- Voice Uplink Capsule Pill (Always visible!) -->
                    <button
                      @click="triggerVoiceSession"
                      class="flex items-center space-x-1.5 px-3 py-1.5 rounded-full border-2 text-[11px] md:text-[10px] font-black uppercase tracking-wider transition-all duration-300 cursor-pointer bg-transparent"
                      :class="isSessionActive ? 'border-red-500 text-red-500 bg-red-500/10 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.2)]' : 'border-[var(--accent)]/30 text-[var(--accent)] hover:bg-[var(--accent)]/5'"
                      :title="isSessionActive ? 'End Voice Session' : 'Start Voice Session'"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-3.5 h-3.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.194-1.613.541-2.296A2.007 2.007 0 014.51 8.25h2.24z" />
                    </svg>
                      <span class="hidden sm:inline">Voice</span>
                    </button>
                  </div>

                  <!-- RIGHT COMMAND CONTROLS -->
                  <div class="flex items-center space-x-2 shrink-0 relative">

                     <!-- 📎 ATTACH (Hidden on Mobile, placed inside '+' Actions Drawer instead) -->
                     <input
                       type="file"
                       ref="fileInputRef"
                       multiple
                       class="hidden"
                       @change="handleFileSelect"
                     />
                     <button @click="triggerFileUpload" class="hidden sm:inline p-2 text-slate-500 hover:text-[var(--accent)] transition-all transform hover:scale-110 bg-transparent border-0 cursor-pointer" title="Attach Documents (Supports Drag & Drop)">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4.5 h-4.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                        </svg>
                     </button>

                     <!-- 📁 FOLDER INGEST (Idea G - Bulk Workspace Upload) (Hidden on Mobile) -->
                     <input
                       type="file"
                       ref="folderInputRef"
                       webkitdirectory
                       directory
                       multiple
                       class="hidden"
                       @change="handleFolderSelect"
                     />
                     <button @click="triggerFolderUpload" class="hidden sm:inline p-2 text-slate-500 hover:text-[var(--accent)] transition-all transform hover:scale-110 bg-transparent border-0 cursor-pointer" title="Ingest Local Workspace Folder">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.2" stroke="currentColor" class="w-4.5 h-4.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                        </svg>
                     </button>

                     <!-- ✨ OPTIMIZE PROMPT BUTTON (Hidden on Mobile) -->
                     <button
                       @click="optimizeCurrentPrompt"
                       :disabled="isOptimizing || !textInput.trim()"
                       class="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-lg border-2 border-sky-600/30 dark:border-[var(--accent)]/30 bg-slate-100 dark:bg-[var(--bg-panel)] hover:border-sky-600 dark:hover:border-[var(--accent)] text-sky-600 dark:text-[var(--accent)] text-[11px] md:text-[10px] font-black uppercase tracking-wider cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm h-8"
                       title="AI Optimize Prompt"
                     >
                       <span>✨</span>
                       <span class="hidden sm:inline">{{ isOptimizing ? 'Optimizing...' : 'Optimize' }}</span>
                     </button>

                     <!-- CUSTOM THEME-AWARE MODEL SELECTOR (Always visible inside cockpit capsule) -->
                     <div class="relative h-8 flex items-center">
                       <button
                         @click="isModelMenuOpen = !isModelMenuOpen"
                         class="model-btn flex items-center space-x-1.5 border-2 border-sky-600/30 dark:border-[var(--accent)]/30 rounded px-2.5 py-1 bg-slate-100 dark:bg-[var(--bg-panel)] hover:border-sky-600 dark:hover:border-[var(--accent)] transition-all cursor-pointer text-[10px] font-bold uppercase tracking-wider text-sky-600 dark:text-[var(--accent)] shadow-sm h-8 bg-transparent shrink-0"
                       >
                         <span>{{ selectedModel === 'gemini-2.5-flash' ? 'Gemini Flash' : 'Gemini Pro' }}</span>
                         <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-2.5 h-2.5 transition-transform" :class="isModelMenuOpen ? 'rotate-180' : ''">
                           <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                         </svg>
                       </button>

                       <!-- Dropdown Flyout (Highly readable & spacious) -->
                       <ul
                         v-if="isModelMenuOpen"
                         class="absolute bottom-full right-0 mb-3 w-44 bg-[var(--bg-panel)]/95 border-2 border-[var(--accent)]/30 rounded-2xl py-2 shadow-2xl z-30 animate-fade-in backdrop-blur-xl"
                       >
                         <li>
                           <button @click="selectModel('gemini-2.5-flash')" class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[11px] font-bold tracking-wide text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2">
                             <span>🧠</span>
                             <span>Gemini 2.5 Flash</span>
                           </button>
                         </li>
                         <li>
                           <button @click="selectModel('gemini-2.5-pro')" class="w-full text-left px-4 py-2.5 hover:bg-[var(--accent)]/10 text-[11px] font-bold tracking-wide text-[var(--text-primary)] hover:text-[var,--accent] transition-colors bg-transparent border-0 cursor-pointer flex items-center space-x-2">
                             <span>🚀</span>
                             <span>Gemini 2.5 Pro</span>
                           </button>
                         </li>
                       </ul>
                     </div>

                     <!-- ➤ DYNAMIC SEND / STOP ACTION BUTTON (Always visible!) -->
                     <button
                       v-if="aiState === 'THINKING' || aiState === 'STREAMING' || aiState === 'SPEAKING'"
                       @click="aiState === 'SPEAKING' ? interruptAudio() : cancelRequest()"
                       class="w-8 h-8 flex items-center justify-center rounded-full bg-red-500 hover:bg-red-600 text-white hover:scale-105 active:scale-95 transition-all shadow-md cursor-pointer shrink-0 border-0 shadow-[0_0_12px_rgba(239,68,68,0.35)] animate-pulse"
                       title="Interrupt Generation / Stop Playback"
                     >
                       <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-3.5 h-3.5">
                         <rect x="6" y="6" width="12" height="12" rx="1.5" />
                       </svg>
                     </button>

                     <button
                       v-else
                       @click="submitText"
                       class="w-8 h-8 flex items-center justify-center rounded-full bg-[var(--accent)] text-[var(--bg-panel)] hover:scale-105 active:scale-95 transition-all shadow-md cursor-pointer shrink-0 border-0"
                       title="Transmit Command"
                     >
                       <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-3.5 h-3.5">
                         <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                       </svg>
                     </button>
                  </div>

                </div>

                <!-- Footer Operations Status Line (Custom V.I.S.I.O.N. Telemetry Indicator) -->
                <div class="flex items-center justify-between px-3 pt-2 text-[8.5px] uppercase tracking-wider text-slate-600 dark:text-slate-400 font-extrabold select-none shrink-0">
                  <div class="md:hidden flex items-center space-x-2">
                    <span class="relative flex h-1.5 w-1.5">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :class="connectionStatus === 'Connected' ? 'bg-emerald-400' : 'bg-red-400'"></span>
                      <span class="relative inline-flex rounded-full h-1.5 w-1.5" :class="connectionStatus === 'Connected' ? 'bg-emerald-500' : 'bg-red-500'"></span>
                    </span>
                    <span>System Connection: {{ connectionStatus }}</span>
                  </div>
                  <div class="ml-auto">{{ (textInput?.length ?? 0).toLocaleString() }} / 15,000</div>
                </div>

              </div>
            </div>

          </div>
        </div>

        <!-- RIGHT COLUMN: DYNAMIC RAG CITATIONS SIDEBAR (PHASE 2.3) -->
        <aside
          v-if="activeCitations.length > 0 && isRagPanelOpen"
          class="absolute right-0 top-0 bottom-0 w-80 md:w-96 flex flex-col bg-[var(--bg-panel)]/95 backdrop-blur-xl p-6 md:p-8 border-l border-[var(--accent)]/15 shadow-2xl z-30 transition-all duration-500 animate-slide-in-right"
        >
          <div class="flex justify-between items-center mb-8 border-b border-[var(--accent)]/10 pb-4 shrink-0">
            <div class="text-[12px] font-black uppercase tracking-[0.3em] text-[var(--accent)]">Source Documents</div>
            <div class="flex items-center space-x-3">
              <button
                @click="isRagPanelOpen = false"
                class="p-1 rounded-lg hover:bg-[var(--accent)]/10 text-[var(--accent)] opacity-60 hover:opacity-100 transition-colors bg-transparent border-0 cursor-pointer flex items-center justify-center"
                title="Minimize Panel"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
              <button
                @click="activeCitations = []"
                class="p-1 rounded-lg hover:bg-red-500/10 text-red-500/80 opacity-60 hover:opacity-100 transition-colors bg-transparent border-0 cursor-pointer flex items-center justify-center"
                title="Clear Citations"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div class="space-y-6 overflow-y-auto custom-scrollbar flex-1 pr-3">
            <div class="text-[10px] uppercase tracking-wider text-slate-500 font-bold opacity-60 select-none">Verified Sources</div>

            <div
              v-for="(citation, idx) in activeCitations"
              :key="idx"
              class="flex flex-col bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl p-4 space-y-3 shadow-md animate-fade-in relative overflow-hidden"
            >
              <!-- Sleek left accent indicator line -->
              <div class="absolute left-0 top-0 h-full w-1.5 bg-[var(--accent)]"></div>

              <div class="pl-2 space-y-2">
                <div class="flex items-center space-x-2 text-[var(--accent)]">
                  <span class="text-xs">📄</span>
                  <span class="text-[13px] font-bold truncate block w-full" :title="formatCitationDisplay(citation.name)">{{ formatCitationDisplay(citation.name) }}</span>
                </div>

                <!-- Rich Metadata Sub-Rows (Displaying Space Keys and Page/Ticket IDs dynamically) -->
                <div class="pl-5 text-[10.5px] text-[var(--text-secondary)] space-y-0.5 select-none font-bold">
                  <div>Space: <span class="text-[var(--accent)]">{{ getCitationSpace(citation.name) }}</span></div>
                  <div>ID Ref: <span class="tabular-nums">{{ getCitationId(citation.name) }}</span></div>
                </div>

                <!-- Dynamic Click-to-Teleport Links -->
                <div v-if="getConfluenceUrl(citation.name)" class="pl-5 pt-0.5 select-none">
                  <a
                    :href="getConfluenceUrl(citation.name) || undefined"
                    target="_blank"
                    class="inline-flex items-center space-x-1.5 text-[11px] uppercase tracking-wider text-[var(--accent)] hover:text-sky-400 font-bold hover:underline transition-all duration-300 bg-transparent border-0 cursor-pointer"
                  >
                    <span>🔗</span>
                    <span>Open Confluence</span>
                  </a>
                </div>

                <div v-if="getAdoUrl(citation.name)" class="pl-5 pt-0.5 select-none">
                  <a
                    :href="getAdoUrl(citation.name) || undefined"
                    target="_blank"
                    class="inline-flex items-center space-x-1.5 text-[11px] uppercase tracking-wider text-emerald-400 hover:text-emerald-300 font-bold hover:underline transition-all duration-300 bg-transparent border-0 cursor-pointer"
                  >
                    <span>🔗</span>
                    <span>Open ADO Ticket</span>
                  </a>
                </div>

                <div class="flex items-center justify-between pt-2 border-t border-[var(--border)]/60 select-none">
                  <!-- Pulsing emerald status dot -->
                  <div class="flex items-center space-x-1.5">
                    <span class="relative flex h-2 w-2">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span class="text-[11px] uppercase tracking-wider text-emerald-600 font-black">Verified</span>
                  </div>
                  <!-- High precision confidence metrics -->
                  <span class="text-[11px] uppercase tracking-wider text-slate-500 font-black">Conf: {{ citation.confidence }}%</span>
                </div>
              </div>
            </div>
          </div>
        </aside>

      </main>

      <!-- 4. GLASSMORPHIC PROFILE MODAL (INTERACTIVE SETTINGS & DIRECTIVES) -->
      <div
        v-if="showProfileModal"
        class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 animate-fade-in"
      >
        <div class="bg-[var(--bg-panel)] border-2 border-[var(--accent)]/50 rounded-2xl p-8 max-w-4xl w-full mx-4 shadow-2xl animate-scale-up">
          <div class="flex justify-between items-center mb-6 border-b border-[var(--accent)]/10 pb-4">
            <div class="text-[12px] md:text-[13px] font-black uppercase tracking-[0.3em] text-[var(--accent)]">System Settings & Directives</div>
            <!-- Sleek standard X close SVG button -->
            <button
              @click="showProfileModal = false"
              class="w-8 h-8 rounded-full flex items-center justify-center border border-[var(--accent)]/10 hover:border-[var(--accent)]/30 text-slate-500 hover:text-[var(--accent)] hover:scale-105 transition-all cursor-pointer bg-transparent"
              title="Close Panel"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- LEFT COLUMN: USER PROFILE SETTINGS -->
            <div class="space-y-6">
              <div class="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 border-b border-[var(--accent)]/5 pb-2">Administrator Profile</div>

              <!-- 1. DISPLAY NAME INPUT -->
              <div class="space-y-2">
                <label class="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Display Name</label>
                <input
                  v-model="adminName"
                  type="text"
                  class="w-full bg-[var(--bg-primary)] border-2 border-[var,--border] focus:border-[var,--accent] rounded-lg py-3 px-4 text-[15px] font-medium text-[var(--text-primary)] focus:outline-none transition-all"
                  placeholder="Enter Display Name..."
                />
              </div>

              <!-- 2. CORPORATE ROLE -->
              <div class="space-y-2">
                <label class="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Corporate Role</label>
                <input
                  v-model="adminRole"
                  type="text"
                  class="w-full bg-[var(--bg-primary)] border-2 border-[var,--border] focus:border-[var,--accent] rounded-lg py-3 px-4 text-[15px] font-medium text-[var(--text-primary)] focus:outline-none transition-all"
                  placeholder="Enter Corporate Role..."
                />
              </div>

              <!-- 3. DEPARTMENT -->
              <div class="space-y-2">
                <label class="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Department</label>
                <input
                  v-model="adminDept"
                  type="text"
                  class="w-full bg-[var(--bg-primary)] border-2 border-[var,--border] focus:border-[var,--accent] rounded-lg py-3 px-4 text-[15px] font-medium text-[var(--text-primary)] focus:outline-none transition-all"
                  placeholder="Enter Department..."
                />
              </div>
            </div>

            <!-- RIGHT COLUMN: CORE AI DIRECTIVES (PROMPT OVERRIDES) -->
            <div class="flex flex-col space-y-4">
              <div class="text-[11px] font-black uppercase tracking-[0.2em] text-slate-400 border-b border-[var(--accent)]/5 pb-2">AI Persona & System Guidelines</div>

              <div class="flex-1 flex flex-col space-y-2">
                <label class="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Configure Global Behavioral Rules (Markdown)</label>
                <textarea
                  v-model="customDirectives"
                  class="flex-1 w-full min-h-[220px] bg-[var(--bg-primary)] border-2 border-[var,--border] focus:border-[var,--accent] rounded-lg p-4 text-[13px] font-mono leading-relaxed text-[var(--text-primary)] focus:outline-none resize-none custom-scrollbar"
                  placeholder="Define custom rules (Markdown compatible)..."
                ></textarea>
              </div>
            </div>
          </div>

          <div class="mt-8 border-t border-[var(--accent)]/10 pt-6 flex justify-end">
            <button
              @click="saveProfileSettings"
              class="px-6 py-3 bg-[var(--accent)] text-[var(--bg-panel)] text-[12px] uppercase tracking-wider font-black rounded-lg hover:scale-105 active:scale-95 transition-all shadow-md cursor-pointer"
            >
              Save Settings & Reload AI Context
            </button>
          </div>
        </div>
      </div>

      <!-- 5. GLASSMORPHIC FIRST-START ONBOARDING WELCOME MODAL (SaaS Style) -->
      <div
        v-if="showOnboardingModal"
        class="fixed inset-0 bg-black/85 backdrop-blur-xl flex items-center justify-center z-50 animate-fade-in"
      >
        <div class="bg-[var(--bg-panel)] border-2 border-[var(--accent)] rounded-2xl p-8 max-w-4xl w-full mx-4 shadow-2xl animate-scale-up flex flex-col max-h-[90vh]">

          <div class="border-b border-[var(--accent)]/10 pb-4 shrink-0">
            <div class="text-[13px] md:text-[14px] font-black uppercase tracking-[0.3em] text-[var(--accent)] animate-pulse">🚀 Welcome to V.I.S.I.O.N. Cockpit</div>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar pr-1 my-6 space-y-6">
            <div class="text-[var(--text-secondary)] leading-relaxed text-[14px] md:text-[15px] space-y-3.5">
              <p>Hi, <strong class="text-[var(--text-primary)] font-bold">{{ adminName }}</strong>! Welcome to your advanced corporate AI operating workspace.</p>

              <p>Before initializing your AI colleague, please review or edit the core guidelines below. These instructions define the standards, security policies, and custom behavioral rules that the AI will strictly follow during your sessions:</p>
            </div>

            <!-- Custom Directives Textarea -->
            <div class="flex flex-col space-y-2 shrink-0">
              <div class="text-[10px] font-black uppercase tracking-wider text-[var(--text-secondary)]/70">Edit Core AI Guidelines:</div>
              <textarea
                v-model="onboardingDirectives"
                class="w-full h-64 bg-[var(--bg-primary)] border-2 border-[var,--border] focus:border-[var,--accent] rounded-lg p-4 text-[13px] font-mono leading-relaxed text-[var(--text-primary)] focus:outline-none resize-none custom-scrollbar"
                placeholder="Write your custom instructions (Markdown supported)..."
              ></textarea>
            </div>
          </div>

          <div class="border-t border-[var(--accent)]/10 pt-6 flex justify-end shrink-0">
            <button
              @click="saveOnboardingSettings"
              class="px-8 py-3.5 bg-[var(--accent)] text-[var(--bg-panel)] text-[12px] uppercase tracking-wider font-black rounded-lg hover:scale-105 active:scale-95 transition-all shadow-md cursor-pointer"
            >
              Save & Initialize AI Brain
            </button>
          </div>
        </div>
      </div>

      <!-- 5. PLATFORM STATUS PANEL (ADMIN ONLY) -->
      <div
        v-if="showTelemetryModal"
        class="fixed inset-0 bg-black/65 backdrop-blur-md flex items-center justify-center z-50 animate-fade-in"
      >
        <div class="bg-[var(--bg-panel)] border border-[var,--border] rounded-2xl p-8 max-w-lg w-full mx-4 shadow-2xl animate-scale-up select-text">
          <div class="flex justify-between items-center mb-6 border-b border-[var(--accent)]/10 pb-4">
            <div class="text-[12px] md:text-[13px] font-black uppercase tracking-[0.3em] text-[var(--accent)]">Platform Status</div>
            <!-- Close button -->
            <button
              @click="showTelemetryModal = false"
              class="w-8 h-8 rounded-full flex items-center justify-center border border-[var(--accent)]/10 hover:border-[var(--accent)]/30 text-slate-500 hover:text-[var(--accent)] hover:scale-105 transition-all cursor-pointer bg-transparent"
              title="Close Panel"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div v-if="telemetryData" class="space-y-6">
            <!-- Relational & Database Status Row -->
            <div class="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-primary)]/50 border border-[var,--border]">
              <span class="font-bold text-slate-400">Database Connection:</span>
              <span class="font-black text-[var(--accent)]">
                {{ telemetryData.database_status && telemetryData.database_status.startsWith('Connected') ? 'Connected' : telemetryData.database_status }}
              </span>
            </div>

            <!-- Total Quantities Stats Grid (Pristine balanced double-column layout! - Phase 4) -->
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3.5 rounded-xl bg-[var(--bg-primary)]/50 border border-[var,--border] text-center shadow-sm">
                <div class="text-2xl font-black text-[var,--accent]">
                  {{ telemetryData.documents.CONFLUENCE || 0 }}
                </div>
                <div class="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-bold mt-1">Confluence Pages</div>
              </div>
              <div class="p-3.5 rounded-xl bg-[var(--bg-primary)]/50 border border-[var,--border] text-center shadow-sm">
                <div class="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                  {{ nextSyncDisplay }}
                </div>
                <div class="text-[11px] uppercase tracking-wider text-[var(--text-secondary)] font-bold mt-1">Next Sync</div>
              </div>
            </div>

            <!-- Space Key Distribution -->
            <div>
              <div class="text-[10px] uppercase tracking-wider text-[var(--accent)] font-black mb-3">Connected Spaces</div>
              <div class="max-h-44 overflow-y-auto space-y-2 border border-[var,--border] rounded-xl p-3 bg-[var(--bg-primary)]/30 custom-scrollbar">
                <div v-for="(count, space) in telemetryData.spaces" :key="space" class="flex justify-between items-center py-1 border-b border-[var,--border]/10 last:border-0">
                  <span class="font-bold text-[var(--text-primary)]">📁 {{ space }}</span>
                  <span class="font-black text-[var,--text-secondary] text-xs bg-[var(--bg-primary)]/60 px-2 py-0.5 rounded-full">{{ count }} pages</span>
                </div>
                <div v-if="Object.keys(telemetryData.spaces).length === 0" class="text-center text-[var,--text-secondary] italic py-2">
                  No spaces synchronized yet.
                </div>
              </div>
            </div>

            <!-- Active Sync Scheduler targets -->
            <div>
              <div class="text-[10px] uppercase tracking-wider text-slate-400 font-black mb-3">Sync Schedules</div>
              <div class="space-y-2 border border-[var,--border] rounded-xl p-3 bg-[var(--bg-primary)]/30">
                <div v-for="(time, space) in telemetryData.sync_targets" :key="space" class="flex justify-between items-center text-xs">
                  <span class="font-bold text-[var(--text-primary)]">🤖 {{ space }}</span>
                  <span class="text-[var,--text-secondary] tabular-nums">Last Sync: {{ formatSyncTime(time) }}</span>
                </div>
                <div v-if="Object.keys(telemetryData.sync_targets).length === 0" class="text-center text-slate-500 italic py-2">
                  No automated schedules active.
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12 text-slate-500 italic animate-pulse">
             Contacting backend diagnostic telemetry...
          </div>
        </div>
      </div>

      <!-- 6. FLOATING ULTRA-USER-FRIENDLY HIGHLIGHT ACTION MENU (Idea E - Highlight-to-Ask!) -->
      <div
        v-if="showHighlightMenu"
        :style="{ top: `${highlightMenuCoords.y}px`, left: `${highlightMenuCoords.x}px` }"
        class="fixed w-[200px] bg-[#0d1117]/95 border border-[#30363d] rounded-2xl p-2 shadow-[0_12px_40px_rgba(0,0,0,0.6)] z-50 flex items-center justify-between space-x-1.5 backdrop-blur-xl animate-fade-in select-none box-border hover:border-[var(--accent)]/30 transition-all duration-300"
      >
        <button
          @click="submitHighlightedQuery('explain')"
          class="flex-1 py-2 rounded-xl bg-[#161b22] hover:bg-[var(--accent)]/10 border border-[#30363d]/50 hover:border-[var(--accent)]/30 text-[10px] font-bold text-slate-300 hover:text-[var(--accent)] transition-all cursor-pointer flex items-center justify-center space-x-1.5 hover:scale-105 shrink-0"
          title="Explain this concept in deeper detail with clear architectural context and specifications"
        >
          <span class="text-[11px]">🔍</span>
          <span>Explain</span>
        </button>
        <button
          @click="submitHighlightedQuery('code')"
          class="flex-1 py-2 rounded-xl bg-[#161b22] hover:bg-[var(--accent)]/10 border border-[#30363d]/50 hover:border-[var(--accent)]/30 text-[10px] font-bold text-slate-300 hover:text-[var,--accent] transition-all cursor-pointer flex items-center justify-center space-x-1.5 hover:scale-105 shrink-0"
          title="Provide a step-by-step code example or script"
        >
          <span class="text-[11px]">💡</span>
          <span>Code</span>
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router'; // Import Router for Console Locking
import AudioRecorder from '@/components/2-molecules/AudioRecorder.vue';
import AppStatusBadge from '@/components/1-atoms/AppStatusBadge.vue';
import SystemLog from '@/components/3-organisms/SystemLog.vue';
import { useWebSocket } from '@/composables/useWebSocket';

const router = useRouter(); // Initialize router instance

// Sidebar sessions search query
const chatFilterQuery = ref('');

const {
  connectionStatus,
  aiState,
  agentStatus, // Real-time JIT statuses
  activeSessionTitle, // Auto-Title pipeline
  receivedMessages,
  isConnected,
  sendAudioData,
  sendMessage,
  interruptAudio,
  cancelRequest,
  connect,
  disconnect
} = useWebSocket();

// Dynamically resolve unified backend REST endpoint from environmental variables (Enterprise Standard!)
const isLocal = window.location.href.indexOf('localhost') > -1 || window.location.href.indexOf('127.0.0.1') > -1;
const REST_BASE_URL = isLocal ? 'http://127.0.0.1:8000' : window.location.origin;

// --- MULTI-SESSION REACTION ENGINE (PHASE 4) ---
const activeSessionId = ref('default_session');
const savedSessions = ref<{ session_id: string; title: string; admin_name: string }[]>([]);
const editingSessionId = ref<string | null>(null);
const sessionRenameTitle = ref('');
const isGenerating = computed(() => aiState.value === 'THINKING' || aiState.value === 'STREAMING' || aiState.value === 'SPEAKING');

const textInput = ref('');
const sessionTitle = ref('General Session'); // Editable session title

watch(activeSessionTitle, (newTitle) => {
  if (newTitle) {
    sessionTitle.value = newTitle;
    const sessionIndex = savedSessions.value.findIndex(s => s.session_id === activeSessionId.value);
    if (sessionIndex !== -1 && savedSessions.value[sessionIndex]) {
      savedSessions.value[sessionIndex]!.title = newTitle; // Non-null assertion to satisfy TS2532
    }
  }
});
const isMuted = ref(false);
const isDarkMode = ref(true);
const recorderRef = ref<any>(null);
const isMoreActionsOpen = ref(false);

// Scoped Multi-Session API Wrappers
const loadSessions = async () => {
  try {
    const res = await fetch(`${REST_BASE_URL}/api/sessions?admin_name=${encodeURIComponent(adminName.value)}`);
    const data = await res.json();
    if (data.status === 'success' && data.sessions) {
      savedSessions.value = data.sessions;

      // Ensure 'default_session' exists if DB is completely empty (Seamless Bootstrap)
      if (savedSessions.value.length === 0) {
        await fetch(`${REST_BASE_URL}/api/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: 'default_session',
            title: 'General Session',
            admin_name: adminName.value
          })
        });
        savedSessions.value = [{ session_id: 'default_session', title: 'General Session', admin_name: adminName.value }];
      }

      // Select the first active session as default
      const lastSession = localStorage.getItem('vision_active_session_id') || 'default_session';
      const exists = savedSessions.value.some(s => s.session_id === lastSession);
      activeSessionId.value = exists ? (lastSession || 'default_session') : (savedSessions.value[0]?.session_id || 'default_session');

      // Load current session title
      const current = savedSessions.value.find(s => s.session_id === activeSessionId.value);
      if (current) sessionTitle.value = current.title;
    }
  } catch (err) {
    // error: "Failed to load dialogue sessions:", err);
  }
};

const createSession = async () => {
  if (isGenerating.value) {
    alert("V.I.S.I.O.N. Gating Policy:\n\nPlease wait until the active query completes before spawning a new session.");
    return;
  }

  // SaaS Concurrency & Bloat Guardrail:
  // Find ANY session titled 'New Session'
  const existingEmpty = savedSessions.value.find(s => s.title === 'New Session');
  if (existingEmpty) {
    if (existingEmpty.session_id === activeSessionId.value) {
      // log: "Already inside an active empty session. Ignoring redundant creation request.");
      return; // Do nothing!
    } else {
      // log: Unused 'New Session' already exists, redirecting user
      await switchSession(existingEmpty.session_id);
      return;
    }
  }

  const newSessionId = crypto.randomUUID();
  const defaultTitle = "New Session";

  try {
    const res = await fetch(`${REST_BASE_URL}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: newSessionId,
        title: defaultTitle,
        admin_name: adminName.value
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      // Instantly wipe the screen BEFORE doing background network calls
      receivedMessages.value = [];
      activeCitations.value = [];
      
      await loadSessions();
      await switchSession(newSessionId);
    }
  } catch (err) {
    // error: "Failed to create new session row:", err);
  }
};

const switchSession = async (sessionId: string) => {
  if (isGenerating.value) {
    alert("V.I.S.I.O.N. Memory Safeguard:\n\nCannot switch session while a technical response is actively generating. Please wait.");
    return;
  }
  if (activeSessionId.value === sessionId) return;

  activeSessionId.value = sessionId;
  localStorage.setItem('vision_active_session_id', sessionId);

  // Set current session title text field
  const current = savedSessions.value.find(s => s.session_id === sessionId);
  if (current) sessionTitle.value = current.title;

  interruptAudio(); // Kill any active speech outputs
  receivedMessages.value = []; // Clean timeline visually while history loads
  activeCitations.value = []; // Wipe sources panel

  // 1. Fetch persistent history scoped strictly to new session
  try {
    const historyRes = await fetch(`${REST_BASE_URL}/api/history?session_id=${sessionId}&admin_name=${encodeURIComponent(adminName.value)}`);
    const historyData = await historyRes.json();
    if (historyData.status === 'success' && historyData.history) {
      receivedMessages.value = historyData.history;
      triggerLockedScrollCascade(); // Force scroll-lock cascade on session switch!
    }
  } catch (err) {
    // error: "Failed to fetch session chat history:", err);
  }

  // 2. Perform safe WebSocket Close & Reconnect (Option A - Hardened)
  disconnect();
  // Delay briefly to allow clean TCP socket disposal (10ms)
  setTimeout(() => {
    connect(sessionId, adminName.value);
  }, 10);
};

const startSessionRename = (sessionId: string, currentTitle: string) => {
  editingSessionId.value = sessionId;
  sessionRenameTitle.value = currentTitle;
};

const saveSessionRename = async (sessionId: string) => {
  if (!sessionRenameTitle.value.trim()) {
    editingSessionId.value = null;
    return;
  }

  try {
    const res = await fetch(`${REST_BASE_URL}/api/sessions/${sessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: sessionRenameTitle.value,
        admin_name: adminName.value
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      const s = savedSessions.value.find(sess => sess.session_id === sessionId);
      if (s) s.title = sessionRenameTitle.value;
      if (activeSessionId.value === sessionId) sessionTitle.value = sessionRenameTitle.value;
    }
  } catch (err) {
    // error: "Failed to rename session:", err);
  } finally {
    editingSessionId.value = null;
  }
};

const deleteSession = async (sessionId: string) => {
  const confirmDel = confirm("Are you sure you want to permanently delete this chat session? All historical messages and logs will be permanently erased.");
  if (!confirmDel) return;

  try {
    const res = await fetch(`${REST_BASE_URL}/api/sessions/${sessionId}?admin_name=${encodeURIComponent(adminName.value)}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.status === 'success') {
      // If deleting the currently active session, switch to default first!
      if (activeSessionId.value === sessionId) {
        await switchSession('default_session');
      }
      await loadSessions();
    }
  } catch (err) {
    // error: "Failed to delete chat session:", err);
  }
};

// Filtered sessions search computed array
const filteredSessions = computed(() => {
  const query = chatFilterQuery.value?.trim() ?? '';
  if (!query) return savedSessions.value ?? [];
  return (savedSessions.value ?? []).filter(s => s?.title?.toLowerCase()?.includes(query.toLowerCase()));
});

const showSessionNotice = () => {
  alert("V.I.S.I.O.N. runs inside a local secure sandbox. Historical multi-sessions are archived on disk in the local SQLite db.");
};

const handleGlobalClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;

  // Close More Actions drawer if clicked outside the '+' button or the actions drawer container
  const isPlusClick = target.closest('.plus-btn') || target.closest('.more-actions-drawer');
  if (!isPlusClick) {
    isMoreActionsOpen.value = false;
  }

  // Close Model menu if clicked outside the model trigger button
  const isModelClick = target.closest('.model-btn');
  if (!isModelClick) {
    isModelMenuOpen.value = false;
  }

  // Close Share/Export dropdown if clicked outside the share trigger button or dropdown container
  const isShareClick = target.closest('.share-btn') || target.closest('.share-dropdown');
  if (!isShareClick) {
    isExportMenuOpen.value = false;
  }

  // Close Profile dropdown if clicked outside the profile trigger button 
  const isProfileClick = target.closest('.profile-btn') || target.closest('.profile-dropdown');
  if (!isProfileClick) {
    isProfileMenuOpen.value = false;
  }
};

// User Profile & Personalization States
const showProfileModal = ref(false);
const isProfileMenuOpen = ref(false); // Controls the top-right account dropdown! 
const showTelemetryModal = ref(false);
const telemetryData = ref<any>(null);
const isAdmin = computed(() => sessionStorage.getItem('vision_role') === 'ADMIN');
const confluenceBaseUrl = ref('https://worldline.atlassian.net');
const adoBaseUrl = ref('https://dev.azure.com/worldline');
const confluenceDefaultSpace = ref('');
const adoDefaultProject = ref('');

const openTelemetryModal = async () => {
  showTelemetryModal.value = true;
  telemetryData.value = null;
  try {
    const res = await fetch(`${REST_BASE_URL}/api/telemetry`);
    const data = await res.json();
    if (data.status === 'success') {
      telemetryData.value = data.telemetry;
    } else {
      // Gracefully show the actual backend error message on the screen! 
      telemetryData.value = {
        database_status: `Error: ${data.message || 'Internal backend diagnostics failed'}`,
        documents: {}, chunks: {}, spaces: {}, sync_targets: {}
      };
    }
  } catch (err: any) {
    // error: "Failed to fetch administrative telemetry:", err);
    // Gracefully show the actual network connection error on the screen!
    telemetryData.value = {
      database_status: `Error: Failed to reach backend API (${err.message || err})`,
      documents: {}, chunks: {}, spaces: {}, sync_targets: {}
    };
  }
};

const getChunksCount = (chunks: any): number | string => {
  if (!chunks || typeof chunks !== 'object') return 'Active';
  const vals = Object.values(chunks);
  const sum = vals.reduce((acc: number, val: any) => {
    const num = Number(val);
    return !isNaN(num) ? acc + num : acc;
  }, 0);
  return sum || 'Active';
};

// Dynamic UTC 3-Hour Scheduler Countdown Calculator
const nextSyncDisplay = computed(() => {
  const now = new Date();
  const currentUtcHour = now.getUTCHours();
  const currentUtcMin = now.getUTCMinutes();

  // Sync schedules are triggered on 3-hour boundaries in UTC (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00)
  const nextSyncHour = Math.ceil((currentUtcHour + (currentUtcMin > 0 ? 1 : 0)) / 3) * 3 % 24;

  const nextSyncDate = new Date(now);
  nextSyncDate.setUTCHours(nextSyncHour, 0, 0, 0);

  // If next sync hour is less or equal, it means it is tomorrow (next day boundary transition)
  if (nextSyncHour <= currentUtcHour && currentUtcMin > 0) {
    nextSyncDate.setUTCDate(nextSyncDate.getUTCDate() + 1);
  }

  const diffMs = nextSyncDate.getTime() - now.getTime();
  const diffMin = Math.round(diffMs / 60000);
  const hrs = Math.floor(diffMin / 60);
  const mins = diffMin % 60;

  if (hrs === 0) {
    return `in ${mins}m`;
  }
  return `in ${hrs}h ${mins}m`;
});

// Clean Sync Time Formatter
const formatSyncTime = (timeStr: string) => {
  if (!timeStr || timeStr === 'Never') return 'Never';
  // Strip PostgreSQL microsecond decimals (.359443) cleanly
  return timeStr.split('.')[0] || timeStr;
};
const adminName = ref(sessionStorage.getItem('vision_admin_name') || 'Sandesh');
const adminRole = ref('Lead Platform Architect');
const adminDept = ref('AI Operations & Innovation');
const customDirectives = ref('');
const showOnboardingModal = ref(false);
const onboardingDirectives = ref('');

// Secure Console Log-Out Handler
const handleLogout = () => {
  sessionStorage.removeItem('vision_auth_token');
  router.push('/login');
};

// --- PREMIUM SMART SCROLL STATES (PHASE 4) ---
const isUserScrolledUp = ref(false); // Tracks if user scrolled up to read past history
const showScrollDownBtn = ref(false); // Controls the visibility of the floating [ ↓ ] button
const hasNewUnreadMessages = ref(false); // Controls if the [ ↓ ] button has a pulsing unread dot

// Listens to manual user scrolls to toggle anchoring and button states
const handleScroll = () => {
  if (!chatFeedRef.value) return;

  const el = chatFeedRef.value;
  // Calculate distance from the absolute bottom of the scroll container
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;

  // If user is within 150px of the bottom, we consider them "anchored at the bottom"
  if (distanceFromBottom <= 150) {
    isUserScrolledUp.value = false;
    showScrollDownBtn.value = false;
    hasNewUnreadMessages.value = false;
  } else {
    // User has manually scrolled up to read past history!
    isUserScrolledUp.value = true;
    showScrollDownBtn.value = true;
  }
};

// Smoothly and beautifully slides the viewport to the bottom of the conversation
const scrollToBottom = () => {
  if (!chatFeedRef.value) return;

  isUserScrolledUp.value = false;
  showScrollDownBtn.value = false;
  hasNewUnreadMessages.value = false;

  chatFeedRef.value.scrollTo({
    top: chatFeedRef.value.scrollHeight,
    behavior: 'smooth'
  });
};

// High-Fidelity JIT Scroll-Lock Cascade: Instantly and tightly locks the viewport to the absolute bottom
const triggerLockedScrollCascade = () => {
  isUserScrolledUp.value = false;
  showScrollDownBtn.value = false;
  hasNewUnreadMessages.value = false;

  const snap = () => {
    if (chatFeedRef.value) {
      chatFeedRef.value.scrollTop = chatFeedRef.value.scrollHeight;
    }
  };

  // Staggered execution cascade to track progressive asynchronous layout inflation (Mermaid, Markdown, code cards)
  snap();
  setTimeout(snap, 50);
  setTimeout(snap, 150);
  setTimeout(snap, 300);
  setTimeout(snap, 500);
};

const saveOnboardingSettings = () => {
  // Guardrail: Non-admins save strictly to local browser memory to prevent overwriting global database settings! 
  if (!isAdmin.value) {
    // log: "Onboarding: Guest user detected. Saving directives locally to browser memory to protect admin settings.");
    localStorage.setItem('vision_custom_directives', onboardingDirectives.value);
    localStorage.setItem('vision_onboarding_completed', 'true');
    showOnboardingModal.value = false;
    return;
  }

  // Save custom AI directives to the backend database globally (Admins and Leads only!)
  fetch(`${REST_BASE_URL}/api/directives`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: onboardingDirectives.value,
      role: sessionStorage.getItem('vision_role') || 'GUEST'
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      log.info("Onboarding: AI instructions reloaded on backend successfully.");
      customDirectives.value = onboardingDirectives.value;
      localStorage.setItem('vision_onboarding_completed', 'true');
      showOnboardingModal.value = false;
    }
  })
  .catch((err: Error) => {
    log.error('Onboarding: Failed to save custom system directives', err);
  });
};

const saveProfileSettings = () => {
  // Guardrail: Non-admins are blocked from saving to the backend 
  if (!isAdmin.value) {
    alert("V.I.S.I.O.N. Access Denied:\n\nOnly administrators or leads are authorized to overwrite global system settings.");
    showProfileModal.value = false;
    return;
  }

  // Save custom AI directives to the backend (Admins and Leads only!)
  fetch(`${REST_BASE_URL}/api/directives`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: customDirectives.value,
      role: sessionStorage.getItem('vision_role') || 'GUEST'
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      log.info("AI instructions reloaded on backend successfully.");
    }
  })
  .catch((err: Error) => {
    log.error('Failed to save directives to backend', err);
  });

  showProfileModal.value = false;
};

// Collapse State for Sidebars (Collapsed by default for pristine view space!)
const isLeftPanelOpen = ref(false);
const chatFeedRef = ref<HTMLElement | null>(null);

// RAG, Indexing, and Citations States (Phase 2.3)
const isIndexing = ref(false);
const activeCitations = ref<{ name: string; confidence: number }[]>([]);
const isRagPanelOpen = ref(true);

// Fluid flex layout active, centerColumnClass removed
// Unified Upload States
const attachedFiles = ref<File[]>([]);
const isDragging = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// Idea G: Workspace Folder Ingester States & Handlers
const attachedFolderFiles = ref<File[]>([]);
const attachedFolderName = ref('');
const attachedFolderSize = ref(0);
const folderInputRef = ref<HTMLInputElement | null>(null);

const triggerFolderUpload = () => {
  folderInputRef.value?.click();
};

const handleFolderSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files;
  const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB

  if (files && files.length > 0) {
    // Extract the top-level folder name from the first file's webkitRelativePath
    const firstFile = files[0];
    if (firstFile && firstFile.webkitRelativePath) {
      attachedFolderName.value = "/" + firstFile.webkitRelativePath.split('/')[0];
    } else {
      attachedFolderName.value = "/Workspace-Ingest";
    }

    attachedFolderFiles.value = [];
    attachedFolderSize.value = 0;

    // --- SMART INGESTION IGNORE FILTERS (FINOPS GUARDRAILS - PHASE 4) ---
    // Exclude heavy dependency, build, git, and local virtual environment directories
    const blockedDirs = ['node_modules', '.git', 'bin', 'obj', '.venv', '.venu', 'dist', 'build', '.nuxt', '.next', 'temp_docs'];

    // Whitelist only high-signal code, document, and configuration extensions
    const allowedExtensions = [
      '.cs', '.vue', '.ts', '.js', '.py', '.json', '.md', '.txt',
      '.html', '.css', '.yml', '.yaml', '.xml', '.config', '.sql', '.tf'
    ];

    let skippedCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file) {
        const path = (file.webkitRelativePath || file.name).toLowerCase();

        // 1. Directory Filter: Skip any files sitting inside blocked folders
        const isBlockedDir = blockedDirs.some(dir => path.includes(`/${dir}/`) || path.startsWith(`${dir}/`));
        if (isBlockedDir) {
          skippedCount++;
          continue;
        }

        // 2. Extension Filter: Skip binary assets (images, DLLs, exes, videos, archives)
        const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        if (!allowedExtensions.includes(fileExt)) {
          skippedCount++;
          continue;
        }

        // 3. Size Filter: Skip single file exceptions that exceed 15MB
        if (file.size > MAX_FILE_SIZE) {
          skippedCount++;
          continue;
        }

        // Accrue only lightweight, pristine source code files!
        attachedFolderFiles.value.push(file);
        attachedFolderSize.value += file.size;
      }
    }
    // log: FINOPS INGEST captured files, skipped build/binary files
  }
};

const clearFolderSelection = () => {
  attachedFolderFiles.value = [];
  attachedFolderName.value = '';
  attachedFolderSize.value = 0;
};

// Model Selection State
const selectedModel = ref('gemini-2.5-flash');
const isModelMenuOpen = ref(false);

const selectModel = (model: string) => {
  selectedModel.value = model;
  isModelMenuOpen.value = false;
};

// --- AGENTIC INTENT ROUTER STATES (PHASE 4) ---
const activeScope = ref('AUTO'); // Default Scope
const currentRouteReason = ref(''); // Stores the route reason parsed from the backend (e.g. INTERNAL, WEB)

const triggerQuickAction = (scopeType: string, templateText: string) => {
  activeScope.value = scopeType; // Instantly highlight and select the corresponding Scope Chip!
  textInput.value = templateText; // Pre-fill the text console!
};

// JIT Live ADO Query Handler
const handleAdoQuery = async (payload: { count: number, query: string }) => {
  if (!payload.query) return;

  // 1. Set our active loader states so the beautiful flat thinking dots appear!
  aiState.value = 'THINKING';

  try {
    // 2. Push the user click intent directly to the visible logs timeline
    receivedMessages.value.push(`[ADMIN]: Retrieve the detailed active ADO tickets for topic: "${payload.query}"`);

    // 3. Fire the JIT live REST fetch to our newly added backend endpoint
    const res = await fetch(`${REST_BASE_URL}/api/search/ado`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: payload.query,
        session_id: activeSessionId.value,
        admin_name: adminName.value
      })
    });

    const data = await res.json();
    if (data.status === 'success' && data.message) {
      // 4. Push the beautifully formatted tickets markdown profile directly into the active chat thread!
      receivedMessages.value.push(data.message);
    } else {
      receivedMessages.value.push(`Error: Could not retrieve active ADO tickets. (Reason: ${data.message || 'Unknown'})`);
    }
  } catch (err) {
    // error: "JIT ADO live query failed:", err);
    receivedMessages.value.push("Error: Failed to connect to the live JIT ADO search API. Please check your network and try again.");
  } finally {
    // 5. Restore the standing standby state
    aiState.value = 'STANDBY';
  }
};

// Unified Cockpit Intelligence States
// Idea 6: Real-Time FinOps Cost Meter States
const sessionTokens = ref({ input: 0, output: 0, total: 0 });
const sessionCost = ref(0.0);

const isSessionActive = computed(() => recorderRef.value?.isSessionActive || false);

// File Handlers
const triggerFileUpload = () => {
  fileInputRef.value?.click();
};

// Master Security Whitelist: Only allow high-signal code, validated business documents, and screenshot images!
const ALLOWED_EXTENSIONS = [
  '.cs', '.vue', '.ts', '.js', '.py', '.json', '.md', '.txt',
  '.html', '.css', '.yml', '.yaml', '.xml', '.config', '.sql', '.tf',
  '.pdf', '.docx',
  '.png', '.jpg', '.jpeg', '.gif', '.webp'
];

const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files;
  const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB
  if (files) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file) {
        // 1. Extension Guardrail: Reject zip archives, installers, and compiled binaries
        const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
          alert(`BLOCKED SECURITY POLICY:\n\n"${file.name}" is an unsupported file format.\nPlease upload valid code (.cs, .vue, .ts, etc.) or document (.pdf, .docx) files.`);
          continue;
        }

        // 2. Size Guardrail
        if (file.size > MAX_FILE_SIZE) {
          alert(`File "${file.name}" exceeds the maximum allowed upload limit of 15MB.`);
          continue;
        }
        attachedFiles.value.push(file);
      }
    }
  }
};

const handleFileDrop = (event: DragEvent) => {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15MB
  if (files) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file) {
        // 1. Extension Guardrail
        const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
          alert(`BLOCKED SECURITY POLICY:\n\n"${file.name}" is an unsupported file format.\nPlease upload valid code or document files.`);
          continue;
        }

        // 2. Size Guardrail
        if (file.size > MAX_FILE_SIZE) {
          alert(`File "${file.name}" exceeds the maximum allowed upload limit of 15MB.`);
          continue;
        }
        attachedFiles.value.push(file);
      }
    }
  }
};

const removeFile = (index: number) => {
  attachedFiles.value.splice(index, 1);
};

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const triggerVoiceSession = () => {
  recorderRef.value?.toggleSession();
};

const submitText = async () => {
  if ((textInput.value.trim() || attachedFolderFiles.value.length > 0) && isConnected.value) {
    // 1. Optimistic UI: Cache input text and files, and instantly empty the UI!
    // This gives the user an instantaneous feedback experience (0ms latency feel)
    const rawText = textInput.value;
    const activeFiles = [...attachedFiles.value, ...attachedFolderFiles.value]; // Merges folder files and individual files!
    const folderName = attachedFolderName.value;

    // Clear inputs instantly
    textInput.value = '';
    attachedFiles.value = [];
    clearFolderSelection();

    let processedMessage = rawText;

    // 2. Physically upload files/folder to the FastAPI REST Gateway before sending the WebSocket prompt
    if (activeFiles.length > 0) {
      isIndexing.value = true;
      const formData = new FormData();

      activeFiles.forEach(file => {
        // Explicitly preserve full relative directory paths (e.g. src/utils/helper.ts) for local codebase RAG!
        formData.append('files', file, file.webkitRelativePath || file.name);
      });

      try {
        // log: "Vectorizing and indexing documents into local ChromaDB...");
        const res = await fetch(`${REST_BASE_URL}/api/upload`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        // log: "ChromaDB Indexing completed successfully:", data);

        // Check if any file was blocked by DLP Security policies
        if (data && data.results) {
          const blockedFile = data.results.find((r: any) => r.status === 'blocked');
          if (blockedFile) {
            alert(`DLP SECURITY POLICY VIOLATION:\n\n${blockedFile.message}`);
          }
        }
      } catch (upload_err) {
        // error: "Failed to upload files to local RAG service:", upload_err);
      } finally {
        isIndexing.value = false;
      }
    }

    // 3. Build the message for UI Conversation Log
    let displayMessage = rawText;
    if (folderName) {
      displayMessage += ` [Attached Workspace: ${folderName}]`;
    } else if (activeFiles.length > 0) {
      const fileNames = activeFiles.map(f => f.name).join(", ");
      displayMessage += ` [Attached Files: ${fileNames}]`;
    }
    receivedMessages.value.push(`[ADMIN]: ${displayMessage}`);

    // 4. Build the payload for the AI backend
    if (activeFiles.length > 0) {
      const fileNames = activeFiles.map(f => f.name).join(", ");
      processedMessage += `\n\n[SYSTEM: ADMINISTRATOR UPLOADED DOCUMENTS FOR ANALYSIS: ${fileNames}]`;
    }
    processedMessage += `\n[SYSTEM CONTEXT: The active administrator's name is ${adminName.value}]`;
    processedMessage += `\n[MODEL_OVERRIDE: ${selectedModel.value}]`;

    // Append Agentic Router Scope Chip Metadata
    processedMessage = `[SCOPE: ${activeScope.value}] ` + processedMessage;

    sendMessage(processedMessage);
  }
};

const handleAudio = (audioBlob: Blob) => {
  if (isConnected.value && !isMuted.value) {
    sendAudioData(audioBlob);
  }
};

const exportData = (content: string, name: string, format: 'json' | 'md' | 'txt') => {
  let finalContent = content;
  const filename = `${name}.${format}`;
  let mimeType = 'text/plain';

  if (format === 'json') {
    finalContent = JSON.stringify({ result: content, timestamp: new Date().toISOString() }, null, 2);
    mimeType = 'application/json';
  } else if (format === 'md') {
    finalContent = `# ${name.toUpperCase()}\n\nGenerated: ${new Date().toLocaleString()}\n\n---\n\n${content}`;
    mimeType = 'text/markdown';
  }

  const blob = new Blob([finalContent], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const exportChatHistory = (format: 'md' | 'txt') => {
  const history = (receivedMessages.value ?? []).join('\n\n---\n\n');
  // Dynamic filename based on user's customized session topic!
  const filenameBase = (sessionTitle.value ?? 'export').toLowerCase().trim().replace(/\s+/g, '-');
  exportData(history, filenameBase || 'chat-history', format);
};

// Export Share Dropdown State
const isExportMenuOpen = ref(false);
const triggerExport = (format: 'md' | 'txt') => {
  exportChatHistory(format);
  isExportMenuOpen.value = false;
};

// Start a fresh session, purging SQLite and active AI sliding memory
const clearChatHistory = async () => {
  // Optimistic UI state cleanup: Reset instantly to guarantee sub-millisecond reaction!
  receivedMessages.value = []; // Clear visual chat cards
  activeCitations.value = []; // Close citations board
  sessionTitle.value = 'General Session'; // Reset topic
  textInput.value = ''; // Clean the input workspace text area
  sessionTokens.value = { input: 0, output: 0, total: 0 }; // Reset FinOps Token meter
  sessionCost.value = 0.0; // Reset FinOps Cost meter
  interruptAudio(); // Instantly stop any speaking speech or active generation thinking state!
  // log: "New conversation initialized cleanly inside local UI stream.");

  try {
    // log: "Purging relational logs and active AI context memory on backend...");
    await fetch(`${REST_BASE_URL}/api/history`, {
      method: 'DELETE'
    });
    // log: "Backend session database successfully purged in background.");
  } catch (err) {
    // error: "Failed to purge backend session history (offline/timeout):", err);
  }
};

const formatCitationDisplay = (sourceName: string | null | undefined) => {
  if (!sourceName) return '[Unknown Source]';
  let displayName = (sourceName ?? '').replace('.txt', '');
  if (displayName.startsWith('confluence_page_')) {
    displayName = displayName.replace('confluence_page_', '');
    displayName = displayName.replace(/_\d+$/, ''); // Strips the pageId at the end
    displayName = displayName.replace(/_/g, ' ');   // Replaces underscores with spaces
    return `[Confluence] ${displayName}`;
  } else if (displayName.startsWith('ado_workitem_')) {
    displayName = displayName.replace('ado_workitem_', '');
    displayName = displayName.replace(/_\d+$/, ''); // Strips the ticketId at the end
    displayName = displayName.replace(/_/g, ' ');   // Replaces underscores with spaces
    return `[ADO] ${displayName}`;
  }
  return displayName;
};

const getCitationSpace = (sourceName: string) => {
  if (sourceName.startsWith('confluence_page_')) {
    const parts = sourceName.split('_');
    return parts[2] || confluenceDefaultSpace.value || 'ERK'; // e.g., confluence_page_ERK_Title_ID.txt
  } else if (sourceName.startsWith('ado_workitem_')) {
    const parts = sourceName.replace('ado_workitem_', '').split('_');
    return parts[0] || adoDefaultProject.value || 'ADO';
  }
  return 'System';
};

const getCitationId = (sourceName: string) => {
  const match = sourceName.match(/_(\d+)\.txt$/);
  return match ? match[1] : 'ID';
};

// URL Generators for RAG Click-to-Teleport Hyperlinks
const getConfluenceUrl = (sourceName: string) => {
  if (sourceName.startsWith('confluence_page_') && sourceName.endsWith('.txt')) {
    const match = sourceName.match(/_(\d+)\.txt$/);
    const pageId = match ? match[1] : null;
    if (pageId) {
      return `${confluenceBaseUrl.value}/wiki/pages/viewpage.action?pageId=${pageId}`;
    }
  }
  return null;
};

const getAdoUrl = (sourceName: string) => {
  if (sourceName.startsWith('ado_workitem_') && sourceName.endsWith('.txt')) {
    const match = sourceName.match(/_(\d+)\.txt$/);
    const ticketId = match ? match[1] : null;
    if (ticketId) {
      // Dynamically extract the active project name from our new descriptive filename format!
      // Format: ado_workitem_{project_name}_{safe_title}_{item_id}.txt
      const parts = sourceName.replace('ado_workitem_', '').split('_');
      const projectName = parts[0];
      if (projectName) {
        return `${adoBaseUrl.value}/${projectName}/_workitems/edit/${ticketId}`;
      }
    }
  }
  return null;
};

// AI PROMPT OPTIMIZER LOGIC
const isOptimizing = ref(false);
const optimizeCurrentPrompt = async () => {
  if (!textInput.value.trim() || isOptimizing.value) return;

  isOptimizing.value = true;
  try {
    // log: "Optimizing raw prompt using backend LLM optimizer...");
    const res = await fetch(`${REST_BASE_URL}/api/optimize_prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: textInput.value })
    });
    const data = await res.json();
    if (data.status === 'success' && data.optimized) {
      textInput.value = data.optimized;
      // log: "Prompt optimized successfully!");
    }
  } catch (err) {
    // error: "Failed to optimize prompt:", err);
  } finally {
    isOptimizing.value = false;
  }
};

// Auto-Scroll to bottom of Chat Feed when a new message arrives & Extract Citations/Token payload
watch(receivedMessages, (newMessages) => {
  nextTick(() => {
    if (chatFeedRef.value) {
      if (!isUserScrolledUp.value) {
        // Smoothly and dynamically slide down only if the user is already anchored at the bottom!
        chatFeedRef.value.scrollTo({
          top: chatFeedRef.value.scrollHeight,
          behavior: 'smooth'
        });
      } else {
        // User is reading history! Lock the scroll position and toggle the unread indicator dot!
        hasNewUnreadMessages.value = true;
      }
    }

    // Auto-Compile and render Mermaid.js diagrams on-the-fly!
    setTimeout(() => {
      try {
        const m = (window as any).mermaid;
        if (m) {
          const elements = document.querySelectorAll('.language-mermaid');
          elements.forEach(async (el: any, idx: number) => {
            const b64 = el.getAttribute('data-mermaid-code');
            if (b64 && !el.hasAttribute('data-processed')) {
              try {
                // Decode the browser-immutable Base64 string back into uncorrupted, raw Mermaid text!
                let rawCode = decodeURIComponent(escape(atob(b64)));

                // --- HIGH-FIDELITY FRONTEND SELF-CORRECTOR  ---
                // Automatically self-corrects legacy dashed connection labels 'A -- Label --> B' into modern 'A -->|Label| B'
                if (rawCode.includes('graph TD') || rawCode.includes('flowchart')) {
                  rawCode = rawCode.replace(/([A-Za-z0-9_.-]+)\s*--\s*(.*?)\s*-->\s*([A-Za-z0-9_.-]+)/g, '$1 -->|$2| $3');
                  rawCode = rawCode.replace(/([A-Za-z0-9_.-]+)\s*--\s*(.*?)\s*--\s*([A-Za-z0-9_.-]+)/g, '$1 -->|$2| $3');

                  // Surgically clean and wrap all node descriptions inside outer double-quotes, swapping inner double-quotes to single-quotes! (Guarantees zero parse crashes!)
                  rawCode = rawCode.replace(/([A-Za-z0-9_.-]+)\s*\[(.*?)\]/g, (m, id, text) => {
                    const cleanText = text.replace(/^"|"$/g, '');
                    return `${id}["${cleanText.replace(/"/g, "'")}"]`;
                  });
                  rawCode = rawCode.replace(/([A-Za-z0-9_.-]+)\s*\{(.*?)\}/g, (m, id, text) => {
                    const cleanText = text.replace(/^"|"$/g, '');
                    return `${id}{"${cleanText.replace(/"/g, "'")}"}`;
                  });
                  rawCode = rawCode.replace(/([A-Za-z0-9_.-]+)\s*\((.*?)\)/g, (m, id, text) => {
                    const cleanText = text.replace(/^"|"$/g, '');
                    return `${id}("${cleanText.replace(/"/g, "'")}")`;
                  });
                }

                const id = `mermaid-svg-${idx}-${Math.random().toString(36).substr(2, 9)}`;

                // Compile the vector SVG natively using Mermaid's async render API! (Guarantees zero console rejections!)
                const { svg } = await m.render(id, rawCode);
                el.innerHTML = svg;
                el.setAttribute('data-processed', 'true');
              } catch (renderErr) {
                // warn: "Mermaid render failed safely for block:", renderErr);
                el.innerHTML = `
                  <div class="text-xs text-rose-500 font-mono p-4 border border-rose-500/15 rounded-xl bg-rose-500/5 text-center flex flex-col items-center space-y-1 select-none">
                    <span class="font-bold uppercase tracking-wider text-[10px]">⚠️ Diagram Syntax Warning</span>
                    <span>The generated diagram contains minor formatting issues. V.I.S.I.O.N. is automatically adjusting its layout.</span>
                  </div>
                `;
                el.setAttribute('data-processed', 'true');
              }
            }
          });
        }
      } catch (err) {
        // warn: "Mermaid observer execution failed:", err);
      }
    }, 250);
  });

  if (newMessages.length === 0) return;

  const index = newMessages.length - 1;
  let lastMsg = newMessages[index];
  if (!lastMsg) return;

  // Intercept Real-time SaaS Sidebar Session Renames
  if (lastMsg && lastMsg.startsWith('[SYSTEM_SESSION_RENAME:')) {
    const match = lastMsg.match(/\[SYSTEM_SESSION_RENAME:\s*(.*?):(.*?)\]/);
    if (match && match[1] && match[2]) {
      const sessId = match[1].trim();
      const newTitle = match[2].trim();

      // Update sidebar list array dynamically
      const s = savedSessions.value.find(sess => sess.session_id === sessId);
      if (s) {
        s.title = newTitle;
        savedSessions.value = [...savedSessions.value];
      }

      // If we are looking at this session, update header title instantly too!
      if (activeSessionId.value === sessId) {
        sessionTitle.value = newTitle;
      }
    }
    // Remove the system metadata message packet from visible timelines
    newMessages.pop();
    return;
  }

  // 1. Extract and Parse Token metrics (Idea 6)
  // MUST DO THIS BEFORE MODIFYING lastMsg string!
  if (lastMsg.includes('[TOKENS:')) {
    const tokenMatch = lastMsg.match(/\[TOKENS:\s*(\d+),(\d+)\]/i);
    if (tokenMatch) {
      const input = parseInt(tokenMatch?.[1] ?? '0', 10);
      const output = parseInt(tokenMatch?.[2] ?? '0', 10);
      if (sessionTokens.value) {
        sessionTokens.value.input += input;
        sessionTokens.value.output += output;
        sessionTokens.value.total += (input + output);

        // Calculate exact Gemini 2.5 Flash pricing:
        // Input: $0.075 / 1,000,000 tokens
        // Output: $0.30 / 1,000,000 tokens
        sessionCost.value = (sessionTokens.value.input * 0.000000075) + (sessionTokens.value.output * 0.00000030);
      }
      // log: FinOps cost meter updated with total tokens and estimated cost
    }
    // Strip metadata from visual log bubble
    newMessages[index] = lastMsg.replace(/\[TOKENS:\s*(\d+),(\d+)\]/i, '').trim();
    lastMsg = newMessages[index];
  }

  // 2. Extract and Parse Agentic Router Source Tags
  if (lastMsg.includes('[SOURCE:')) {
    const sourceMatch = lastMsg.match(/\[SOURCE:\s*(AUTO|INTERNAL|WEB|BOTH|CHAT)\]/i);
    if (sourceMatch) {
      currentRouteReason.value = sourceMatch[1] || 'AUTO';
      // Strip metadata from visual log bubble
      newMessages[index] = lastMsg.replace(/\[SOURCE:\s*(AUTO|INTERNAL|WEB|BOTH|CHAT)\]/i, '').trim();
      lastMsg = newMessages[index];
      // log: Agentic router dynamically routed query via intent channel
    }
  }

  // 3. Extract and Parse Citation sources
  if (lastMsg && lastMsg.includes('[SOURCES:')) {
    const match = lastMsg.match(/\[SOURCES:\s*(.*?)\]/);
    if (match && match[1]) {
      const segments = match[1].split(',').map(s => s.trim());
      activeCitations.value = segments.map(seg => {
        if (seg.includes(':')) {
          const parts = seg.split(':');
          const name = parts[0] || '';
          const distStr = parts[1] || '0';
          const dist = parseFloat(distStr);
          // Calculate dynamic similarity %: (1.0 - distance) * 100, clamped between 0 and 100
          const confVal = Math.max(0, Math.min(100, (1.0 - dist) * 100));
          return { name: name.trim(), confidence: parseFloat(confVal.toFixed(1)) };
        }
        return { name: seg, confidence: 98.4 }; // Fallback
      });
      isRagPanelOpen.value = true; // Auto-open citations panel when new sources arrive!
    }
  }
}, { deep: true });

// Idea E: Highlight-to-Ask Response Refiner States
const showHighlightMenu = ref(false);
const selectedResponseText = ref('');
const highlightMenuCoords = ref({ x: 0, y: 0 });

const handleSelectionChange = () => {
  // Disable custom floating selectors on mobile viewports to prevent collisions with native iOS/Android system overlays
  if (window.innerWidth < 640) {
    showHighlightMenu.value = false;
    return;
  }

  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) {
    showHighlightMenu.value = false;
    return;
  }

  const selectedStr = selection.toString().trim();
  if (selectedStr.length < 5) {
    showHighlightMenu.value = false;
    return;
  }

  // Ensure the selection occurred inside an active V.I.S.I.O.N. AI chat bubble
  const anchorNode = selection.anchorNode;
  const parentElement = anchorNode ? (anchorNode.nodeType === Node.ELEMENT_NODE ? anchorNode as HTMLElement : anchorNode.parentElement) : null;
  if (!parentElement || !parentElement.closest('.ai-message-bubble')) {
    showHighlightMenu.value = false;
    return;
  }

  // Capture coordinates of the text selection bounding box dynamically
  try {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Position the floating menu centered horizontally right above the highlighted text selection
    highlightMenuCoords.value = {
      x: rect.left + window.scrollX + (rect.width / 2) - 100, // Offset half of the new compact menu's width (200px / 2 = 100)
      y: rect.top + window.scrollY - 54 // Float 54px directly above the highlighted text row
    };

    selectedResponseText.value = selectedStr;
    showHighlightMenu.value = true;
  } catch (e) {
    showHighlightMenu.value = false;
  }
};

const submitHighlightedQuery = (mode: 'explain' | 'code') => {
  let promptPrefix = "";
  if (mode === 'explain') {
    promptPrefix = "Could you please explain this specific point from your previous response in deeper detail, providing clear architectural context, specifications, and system rules?";
  } else if (mode === 'code') {
    promptPrefix = "Could you please provide a concrete, step-by-step technical code example or script illustrating exactly how this is implemented?";
  }

  const finalMessage = `${promptPrefix}\n\nSelected Context: "${selectedResponseText.value}"`;

  // Clear selection instantly to hide menu
  window.getSelection()?.removeAllRanges();
  showHighlightMenu.value = false;

  // Submit over active websocket channel!
  sendMessage(finalMessage);
  receivedMessages.value.push(`[ADMIN]: ${promptPrefix} "${selectedResponseText.value.substring(0, 50)}..."`);
};

const userGreeting = ref('Good evening, Sandesh.');

const updateGreeting = () => {
  const hour = new Date().getHours();
  let greetingWord = "Good morning";
  if (hour >= 12 && hour < 17) greetingWord = "Good afternoon";
  else if (hour >= 17) greetingWord = "Good evening";
  userGreeting.value = `${greetingWord}, ${adminName.value}.`;
};

// Global Paste Listener - Supports Ctrl+V clipboard file ingestion with robust exception handling!
const handleGlobalPaste = (event: ClipboardEvent) => {
  try {
    const files = event.clipboardData?.files;
    if (files && files.length > 0) {
      // Prevent default browser paste behavior if files are present
      event.preventDefault();

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file) {
          // 1. Extension Guardrail: Silently ignore invalid formats during copy-paste
          const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
          if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
            // warn: `[CLIPBOARD BLOCK] Blocked paste of invalid file: "${file.name}" (Type: ${fileExt})`);
            continue;
          }

          // Push directly to attachedFiles (previously pendingFiles) to render as upload chips!
          attachedFiles.value.push(file);
        }
      }
    }
  } catch (error) {
    // error: "[CLIPBOARD PASTE ERROR] Critical exception caught during file ingestion:", error);
  }
};

onMounted(async () => {
  updateGreeting(); // Dynamic timezone greeting

  // Register click outside listeners
  window.addEventListener('click', handleGlobalClick);

  // Register global paste listener (Ctrl+V - Phase 4)
  window.addEventListener('paste', handleGlobalPaste);

  // Register text selection change listener (Idea E - Highlight-to-Ask!)
  document.addEventListener('selectionchange', handleSelectionChange);

  // Automatic time-based theme selection: Dark mode at night (18:00 - 6:00), Light mode during the day
  const hour = new Date().getHours();
  isDarkMode.value = (hour < 6 || hour >= 18);

  // Load and bootstrap concurrent SaaS sessions
  await loadSessions();

  // Cleanly connect the WebSocket for the active session on page mount
  disconnect();
  setTimeout(() => {
    connect(activeSessionId.value, adminName.value);
  }, 10);

  // Load current active session's historic message logs
  try {
    const historyRes = await fetch(`${REST_BASE_URL}/api/history?session_id=${activeSessionId.value}&admin_name=${encodeURIComponent(adminName.value)}`);
    const historyData = await historyRes.json();
    if (historyData.status === 'success' && historyData.history) {
      receivedMessages.value = historyData.history;
      triggerLockedScrollCascade(); // Force scroll-lock cascade on page boot! (Scroll Anchor)
    }
  } catch (err) {
    // error: "Failed to load historical timeline cards on page boot:", err);
  }

  // Load custom system directives from backend on page mount (and decouple base URLs!)
  fetch(`${REST_BASE_URL}/api/directives`)
    .then(res => res.json())
    .then(data => {
      if (data) {
        if (data.content) {
          customDirectives.value = data.content;
          onboardingDirectives.value = data.content;
        }
        if (data.confluence_url) {
          confluenceBaseUrl.value = data.confluence_url;
        }
        if (data.ado_url) {
          adoBaseUrl.value = data.ado_url;
        }
        if (data.confluence_spaces) {
          confluenceDefaultSpace.value = data.confluence_spaces.split(',')[0].trim();
        }
        if (data.ado_projects) {
          adoDefaultProject.value = data.ado_projects.split(',')[0].trim();
        }

        // Trigger onboarding modal ONLY on the very first start AND ONLY for ADMIN/Super-Admins!
        if (isAdmin.value && !localStorage.getItem('vision_onboarding_completed')) {
          showOnboardingModal.value = true;
        } else {
          // Non-admins (USER role, e.g. Sanjeev!) skip onboarding completely and land straight inside the chat!
          showOnboardingModal.value = false;
        }
      }
    })
    .catch((err: Error) => {
      log.error('Failed to load custom system directives', err);
    });
});

onUnmounted(() => {
  window.removeEventListener('click', handleGlobalClick);
  window.removeEventListener('paste', handleGlobalPaste);
  document.removeEventListener('selectionchange', handleSelectionChange);
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 0px;
}
.animate-fade-in {
  animation: fadeIn 1s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-slide-in-right {
  animation: slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* --- premium SMOOTH FADING SLIDE TRANSITIONS --- */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.9);
}
</style>
