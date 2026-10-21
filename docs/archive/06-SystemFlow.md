# V.I.S.I.O.N. Functional Flow & Platform User Guide

Welcome to the official, step-by-step user guide for the **V.I.S.I.O.N. (Virtual Intelligent System & Platform Mentor) operating cockpit.**

This document provides a highly detailed, comprehensive walk-through of the end-to-end user journey, explaining exactly how each feature operates under the hood to ensure secure, rapid, and precise enterprise assistance.

---

## 1. The Core Functional Workflow

```
[ STEP 1: Secure Entrance ] ➔ User enters passcode ('vision@1133', 'vision@lead', or 'vision2026').
             │
[ STEP 2: Intent Selection ] ➔ User selects a Scope Chip (Auto, Internal, Web, Both) or uses '@web'.
             │
[ STEP 3: In-Memory Bypasses]➔ Greetings (0.1ms) or Ticket IDs are intercepted instantly.
             │
[ STEP 4: Routing Execution] ➔ 4-Way Router branches across strict Internal RAG or Web Grounding.
             │
[ STEP 5: Progressive Fallback]➔ If Auto mode confidence is low, V.I.S.I.O.N. pauses and asks for clarification.
             │
[ STEP 6: Analytical Synthesis]➔ AI analyzes evidence, renders inline diagrams, and displays cost metrics.
             │
[ STEP 7: Secure Session Exit] ➔ Closing tab auto-locks, or user clicks 'Lock Console' to lock.
```

---

## 2. Step-by-Step Functional Guide

### Phase 1: Secure Entrance & Triple-Tier Initialization
*   **The Experience:** When a user opens V.I.S.I.O.N., they do not see the dashboard. Instead, they are greeted by an ultra-premium, dark-glassmorphic login gate featuring a slowly spinning cybernetic core logo, set against a mysterious dark void with softly pulsing ambient cloud nodes.
*   **How it Works:** 
    1.  The Vue Router enforces a strict navigation guard (`router.beforeEach`). It checks if a secure authentication token and role exist in `sessionStorage`. 
    2.  If missing, the router forcefully intercepts the request and blocks the cockpit from even rendering in the DOM, keeping your unique interface a 100% complete surprise!
    3.  The user must type their **Login ID / Name** and a **Passcode**. V.I.S.I.O.N. dynamically evaluates the passcode against three strict login tiers:
        *   **ADMIN (Passcode: `vision@1133`):** Grants full access to the AI Chat and unlocks the interactive **Admin Telemetry Cockpit** (clicking the green 'Connected' badge reveals live system/database statuses).
        *   **LEAD (Passcode: `vision@lead`):** Grants full access to the AI Chat, but keeps the Admin Telemetry Cockpit securely locked.
        *   **GUEST (Passcode: `vision2026`):** Triggers our **Honeypot Decoy Gating**, routing the user to `/guest` where they see a highly realistic, read-only Evoke.Kiosk.RailTVM Fleet Telemetry dashboard, completely camouflaging the real application.
    4.  Upon successful submission of a valid passcode, the system writes the name, token, and role to `sessionStorage` and swaps pages in less than **1 millisecond**, instantly lighting up your glorious operating cockpit!

---

### Phase 2: Dynamic Intent Selection
*   **The Experience:** Once inside, the user has total control over where V.I.S.I.O.N. gathers its evidence. They do not have to let the model "guess" what they mean.
*   **How it Works:**
    *   **The Scope Chips:** A row of 4 selectable glassmorphic pills sits right above the chat input box:
        *   `🧠 Auto (Default)`: Let V.I.S.I.O.N. use progressive confidence checks to decide.
        *   `🏢 Internal Docs`: Force the system to query strictly Confluence pages and ADO tickets under 100% corporate privacy bounds (totally blocking Google Search tools).
        *   `🌐 Web Search`: Force the system to bypass your local database completely, saving 2 seconds of latency, and ground answers using live public Google Search.
        *   `📚 Both (Hybrid)`: Force the system to retrieve your internal specifications, activate web search simultaneously, and critically contrast your corporate policies against the live internet.
    *   **The `@` Shortcuts:** Power users can bypass clicking. Simply start any message with `@web `, `@internal `, or `@both ` in the chat box. The Python backend instantly intercepts the tag, strips it from your query, and forces that specific routing branch!

---

### Phase 3: The Query & Progressive Clarification
When the user clicks "Send", V.I.S.I.O.N.'s 4-way routing engine executes a multi-stage progressive check to ensure maximum speed and safety:

1.  **Fast-Path Greetings Interceptor (0.1ms Speed):**
    *   If the user typed a conversational filler (like *"Hi"*, *"Good morning"*, or *"test"*), V.I.S.I.O.N. intercepts it instantly in local Python memory. It skips all database searches and cloud calls, returning an elegant, on-brand welcoming greeting in less than 1 millisecond at **exactly $0.00 cost** (marked as `Tokens: 0`).
2.  **Exact-Match Alphanumeric Bypass:**
    *   If the user prompt contains an explicit ticket ID (like `59912` or `ADO 60127`), the backend regex catches it and automatically overrides the `Auto` setting to force the `INTERNAL` RAG route, ensuring direct document retrieval.
3.  **Progressive Confidence Checks (The "Auto" Safeguard):**
    *   If set to `Auto`, V.I.S.I.O.N. runs a cheap, super-fast (0.1s) metadata scan of ChromaDB. 
    *   **High Confidence (Distance <= 0.6):** It automatically routes your query to `INTERNAL` RAG to fetch your Confluence data.
    *   **Low Confidence (Distance > 0.6):** V.I.S.I.O.N. refuses to guess (eliminating hallucination risk). Instead, it pauses, saves your query in memory, and politely asks:
        > *"I couldn't find strong internal evidence for that inside our Confluence or ADO database. Would you like me to broaden the search or check the public web?"*
    *   If you type **"Yes"** on the next turn, V.I.S.I.O.N. automatically recalls your original question, activates `self.model_web` with the Google Search Tool, and fetches the answer instantly!

---

### Phase 4: Analytical Synthesis & Image Rendering
*   **The Experience:** V.I.S.I.O.N. does not just dump unformatted, boring paragraphs or parrot raw Confluence text. It delivers highly structured, deeply analytical principal-level engineering assessments, complete with inline architecture diagrams!
*   **How it Works:**
    1.  **Grounded Answer Policy:** Our strict AI instructions force Gemini to only base its answers on the retrieved context. If evidence is missing, it admits it.
    2.  **Parent-Document Collapsing:** Instead of reading tiny, disjointed text chunks, V.I.S.I.O.N. automatically collapses matched vector segments, reconstructs the **entire original 10-page Confluence document** from your SQLite store, and reads the full, unbroken context.
    3.  **Inline Diagram Rendering:** Our custom `HTMLToMarkdownParser` automatically extracts `<img src="...">` tags during Confluence syncing and translates them into Markdown `![Diagram](url)`. V.I.S.I.O.N. then renders these diagrams directly inside your visual chat feed!
    4.  **Route Reason & Cost Transparency:** The UI automatically displays a glowing routing badge above your message box showing exactly why and where the AI gathered its evidence (e.g., `Route: Live Public Internet` or `Route: Internal Knowledge Store`), while your **FinOps Cost Meter** calculates and displays your running session cost in real-time.
    5.  **Conversational Citations & Descriptive Filenames:** When synchronizing, V.I.S.I.O.N. writes parent documents with highly descriptive filenames (such as `confluence_page_PROJWT_PageTitle_ID.txt`). When displaying citations, the Vue frontend parses these descriptive names using a robust regex and transforms them into elegant UI blocks (e.g., 📄 `[Confluence] PROJWT Page Title`), preserving structural clarity while linking back to source identifiers.

---

### Phase 5: Secure Exit & Auto-Locking
*   **The Experience:** When you are done testing, you can confidently walk away from your desk, knowing your cockpit is perfectly secure.
*   **How it Works:**
    *   **Automatic Auto-Lock:** Because we transitioned all token states to `sessionStorage`, your session is tightly bound to your browser tab. **The exact second you close your browser tab, your session is permanently erased!** Reopening the tab will immediately force a login check.
    *   **Manual Console Lock:** You can lock the cockpit in 1 click! Click the glowing red **`[ 🔒 Lock Console ]`** button at the bottom of your left sidebar. Vue instantly clears your session keys, redirects you, and returns you to the stunning, spinning cybernetic login screen, keeping your proprietary project safe from prying eyes!

---

### Phase 6: Immersive HUD Visual Polish & Admin Cockpit
*   **The Experience:** V.I.S.I.O.N.'s HUD has been completely redesigned with a gorgeous, high-contrast, premium dark theme that feels modern, alive, and polished.
*   **How it Works:**
    1.  **Immersive Staggered Chat Layout:** Inside `SystemLog.vue`, the chat feed features a beautiful, staggered chat thread. Bubbles are narrower, bounded by 1px thin borders, and utilize custom styled avatars (a glowing neural "V" circle for AI responses and the user's initials for human messages) to make interactions feel active and conversation-centric.
    2.  **Premium Theme-Aware Cards:** The main welcome dashboard is fixed and widened to `max-w-5xl` for robust horizontal alignment. The four quick start cards are fully styled with glassmorphic CSS variables, featuring solid left-border accent lines that elevate and float on hover and visually compress on click.
    3.  **Admin Telemetry Cockpit:** In `HomeView.vue`, clicking on the green pulsing **`Connected`** status badge opens a stunning glassmorphic **Platform Status** modal. Accessible strictly in **ADMIN** mode, it displays the real-time PostgreSQL database connection status, independent counts of ingested Confluence pages and ADO tickets, and list of active sync targets, providing unparalleled observability into the cockpit's runtime health.

---
*(End of System Flow & User Guide)*