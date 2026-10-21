# 🌊 Project J.A.R.V.I.S. - Sequence Diagrams

This document visually represents the flow of data through the system for key user actions.

## 1. WebSocket "Echo" Handshake (Phase 1)

*This diagram illustrates the initial connection and test message flow.*

```mermaid
sequenceDiagram
    participant User
    participant Frontend (Vue)
    participant Backend (FastAPI)

    User->>Frontend (Vue): Clicks "Send Echo" button
    Frontend (Vue)->>Backend (FastAPI): Establishes WebSocket connection at /ws/audio
    Backend (FastAPI)-->>Frontend (Vue): Connection Accepted
    Frontend (Vue)->>Backend (FastAPI): Sends text message (e.g., "Hello")
    Backend (FastAPI)-->>Frontend (Vue): Echoes message back (e.g., "Echo: Hello")
    Frontend (Vue)->>User: Displays echoed message on screen
(More diagrams for audio streaming, RAG, etc., will be added here.)

javascript
*(Note: VS Code has extensions like "Markdown Mermaid" to render these diagrams.)*

---
## 2. Frontend Audio Capture & Send (Task #2)

```mermaid
sequenceDiagram
    participant User
    participant AudioRecorder.vue
    participant HomeView.vue
    participant useWebSocket.ts
    participant Backend

    User->>AudioRecorder.vue: Clicks Record Button
    AudioRecorder.vue->>Browser API: navigator.mediaDevices.getUserMedia()
    Browser API-->>User: Asks for Microphone Permission
    User-->>Browser API: Allows Permission
    AudioRecorder.vue->>Browser API: mediaRecorder.start()
    User->>Browser API: Speaks "Hello Jarvis"
    User->>AudioRecorder.vue: Clicks Stop Button
    AudioRecorder.vue->>Browser API: mediaRecorder.stop()
    Browser API-->>AudioRecorder.vue: Fires 'onstop' event with audioBlob
    AudioRecorder.vue->>HomeView.vue: Emits 'audio-recorded' event with audioBlob
    HomeView.vue->>useWebSocket.ts: Calls sendAudioData(audioBlob)
    useWebSocket.ts->>Backend: Sends binary audioBlob over WebSocket
    Backend-->>Backend: Throws 'TypeError' (Expected Error)


#### **Protocol Spec & Glossary**
Create `/docs/03-ProtocolSpec.md` and `/docs/05-Glossary.md` with just a title for now. We will fill them in as we build those features.

Example `/docs/05-Glossary.md`:
```markdown
# 📖 Project J.A.R.V.I.S. - Glossary

*   **HUD:** The Vue.js Frontend Interface.
*   **Nervous System:** The FastAPI Backend.
*   ...