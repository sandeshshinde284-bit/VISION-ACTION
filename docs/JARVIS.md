# 📄 Project J.A.R.V.I.S. (Rail Executive Assistant)
## **System Design Document v1.3 (Final)**

| | |
| :--- | :--- |
| **Status:** | **Final - Ready for Project Kickoff** |
| **Version:** | 1.3 |
| **Date:** | October 26, 2023 |
| **Author(s):** | Lead Engineering |
| **Stakeholders:** | Engineering Leadership, Development Team |

---

### **1. Executive Summary**

Project J.A.R.V.I.S. is a voice-first, AI-powered executive assistant designed to augment the capabilities of a modern development team. Its primary mission is to eliminate "institutional blindness" by acting as a living knowledge base, a hands-free developer workspace, and a proactive system monitor. This document serves as the definitive "Source of Truth" for the system's architecture, functional scope, and implementation strategy, incorporating critical feedback to ensure the resulting product is secure, scalable, and compliant with enterprise standards.

### **2. Guiding Principles & Phased Roadmap**

We are adopting a **Strict MVP (Minimum Viable Product)** approach to deliver value incrementally and manage technical risk. Ambitious features are explicitly deferred to later phases.

| Phase | Title | Key Deliverables |
| :--- | :--- | :--- |
| **Phase 1** | **The Foundation** | • Basic bidirectional audio streaming (Vue 3 ↔ FastAPI ↔ Gemini).<br>• Secure local execution sandbox (`SecureExecutionProxy`).<br>• Initial "Hello, World" conversational loop. |
| **Phase 2**| **The Bible & The Tools** | • **Knowledge Retrieval (RAG):** Confluence/ADO document ingestion into `pgvector`.<br>• **Tool Integration:** Implement MCP client to interact with ADO work items.<br>• **Enhanced UX:** Full implementation of audio barge-in support. |
| **Phase 3**| **The Moonshots** | • **Predictive Monitoring:** Live log analysis for proactive issue detection.<br>• **Document Reconstruction:** *[STRETCH GOAL]* Synthesize documentation from Git history. |

### **3. System Architecture**

#### **3.1. High-Level Architectural Diagram**
```
   +--------------------------------------------+
   |             Vue 3 HUD Client               |
   | (Audio Visualizers, Logs, Input)           |
   +--------------------------------------------+
                          ^
                          |  WebSockets (Bidirectional Audio + JSON Events)
                          v
   +--------------------------------------------+
   |         FastAPI Backend Orchestrator       |
   +--------------------------------------------+
       |                  |                 |
       | MCP (JSON-RPC)   | Gemini Live SDK | SQL/pgvector
       v                  v                 v
+--------------+   +---------------+   +------------+
|  MCP Server  |   |  Gemini 3.5   |   | PostgreSQL |
| (Confluence/ |   |  Flash Live   |   | Vector DB  |
|      ADO)    |   |  API          |   |            |
+--------------+   +---------------+   +------------+
       ^
       | CLI Calls via Secure Proxy
       v
+---------------------------------+
| Local Filesystem & Git          |
| (via SecureExecutionProxy)      |
+---------------------------------+
```

#### **3.2. Component Breakdown (The Stack)**

| Layer | Technology | Role / Purpose |
| :--- | :--- | :--- |
| **Frontend (FE)** | **Vue 3 (Vite, Pinia)** | **HUD (Heads-Up Display):** Interactive dashboard for real-time audio visualization, logs, and status. Manages microphone access and VAD for barge-in. |
| **Backend (BE)** | **FastAPI (Python 3.10+)** | **The Nervous System:** Manages WebSocket streams, orchestrates calls to AIs and tools, and enforces security via the `SecureExecutionProxy`. |
| **Primary AI** | **Gemini 3.5 Flash (Live API)** | **The Persona:** Handles real-time, low-latency, bidirectional audio dialogue and core reasoning. |
| **Execution AI** | **Gemini CLI / API** | **The Hands:** Secondary model instance whose output is **strictly passed to the `SecureExecutionProxy`**, not a raw shell. |
| **Knowledge Base** | **PostgreSQL + pgvector** | **The Brain:** Provides long-term memory via semantic storage of documentation for Retrieval-Augmented Generation (RAG). |
| **Protocol** | **Model Context Protocol (MCP)** | **The Connectors:** Open-source standard (JSON-RPC 2.0) to expose enterprise tools (Confluence, ADO) to the AI as standardized resources and functions. |

### **4. Detailed Sub-System Design & Risk Mitigation**

This section addresses the initial technical risks and details their solutions.

*   **Execution Sub-System: The Sandbox**
    *   **Risk:** Granting an AI direct shell access is a critical security vulnerability.
    *   **Mitigation:** All local actions are brokered through a `SecureExecutionProxy` class with command whitelisting and path sanitization. J.A.R.V.I.S. **never** gets raw shell access.

*   **Knowledge Protocol: Model Context Protocol (MCP)**
    *   **Risk:** Creating a proprietary protocol is time-consuming and unnecessary.
    *   **Mitigation:** We will adopt the open-source MCP standard, implementing a client in FastAPI to connect to standard MCP servers for Confluence and ADO.

*   **Conversational UX: Real-time Audio Barge-In**
    *   **Risk:** Achieving seamless interruption is technically challenging.
    *   **Mitigation:** We will use the native bidirectional streaming of the **Gemini Multimodal Live API**. The frontend will use VAD to detect user speech and send a `client_cancel` frame to the backend to instantly halt the AI's audio stream.

### **5. Functional Design (The Use Cases)**

*   **The Confluence Bible:** J.A.R.V.I.S. crawls Confluence/ADO, allowing users to ask natural language questions about institutional knowledge (e.g., *"Why did we use this specific NFC protocol in 2022?"*).
*   **Voice-First Developer Workspace:** Hands-free multitasking (e.g., *"vision, review my current branch for security risks while I grab a coffee."*).
*   **The Fleet Guardian:** Proactively tails hardware logs, detects failure patterns, and drafts fix tickets (e.g., *"Kiosk 402 is failing. I've analyzed the logs and drafted a fix ticket. Should I submit?"*).

### **6. Installation & Prerequisites**

*   **Environment:** Linux/macOS or Windows/WSL2, Node.js v18+, Python v3.10+, Docker.
*   **Credentials:** Google AI Studio API Key, Azure DevOps PAT, Confluence API Token.
*   **Setup:** Standard `docker`, `pip install`, and `npm install` workflows, configured via a `.env` file.

### **7. Non-Functional Requirements**

*   **Privacy:** Use **Google AI Studio** for dev and **Vertex AI** for production to ensure **Zero Data Training** and enterprise data isolation.
*   **Cost Efficiency:** Use **Gemini 3.5 Flash** for its performance-to-cost ratio. Implement a **Redis cache** for RAG queries to reduce redundant embedding and retrieval costs.

### **8. Development & Operational Plan**

*   **Testing:** Multi-layered strategy including Unit (`pytest`, `Vitest`), Integration (`pytest`), E2E (`Playwright`), and a specific **AI Evaluation** suite with a "golden dataset" and guardrail tests.
*   **CI/CD:** Trunk-based development on Git. PRs trigger a CI pipeline for linting, testing, and building. Merges to `main` deploy to a `staging` environment.
*   **Data Ingestion:** Initial bulk ingestion script for RAG, followed by a webhook-based system for incremental updates from Confluence/ADO to keep the knowledge base fresh.
*   **Monitoring:** APM with `OpenTelemetry` to track latency and errors. Cost monitoring by logging token counts for all AI calls. Centralized, structured logging.
*   **Secrets Management:** `.env` files for local dev; **Azure Key Vault** (or similar) for staging/production environments.

### **9. Final Risk Assessment**

Beyond the initial technical risks, the following project-level risks must be managed.

| Risk Category | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **AI Reliability** | **Hallucination:** The AI might confidently provide incorrect information based on a misinterpretation of documents, which is more dangerous than providing no answer. | **Implement Citations:** For every answer sourced from the knowledge base, J.A.R.V.I.S. must provide a direct link to the source Confluence page or ADO ticket. This allows users to verify information instantly. |
| **User Adoption** | **Workflow Friction:** Developers may find the voice interface novel but ultimately slower than their existing keyboard-driven workflows, leading to low adoption after the initial "cool factor" wears off. | **Focus on a "Pilot Group":** Start with a small, enthusiastic group of champion developers. Focus on solving 1-2 of their highest-pain-point tasks perfectly. Gather feedback early and iterate before a wider rollout. |
| **Cost Management** | **Uncontrolled Spend:** While Gemini Flash is cost-effective, high user adoption or inefficient prompting could lead to unexpected and significant API costs. | **Implement Strict Budget Alerts:** In addition to monitoring, set up automated alerts in the cloud billing account that trigger when costs exceed a predefined daily or weekly threshold. Implement user-level rate limiting if necessary. |
| **External Dependency** | **API Changes & Stability:** The project relies heavily on the Gemini Live API and the MCP standard. Breaking changes, outages, or deprecation of these external dependencies could halt development. | **Build an Abstraction Layer:** All external API calls (especially to the Gemini model) will be wrapped in our own internal service class. This "anti-corruption layer" will allow us to adapt to API changes or even swap out the underlying model provider with minimal refactoring. |
| **Performance** | **Perceived Latency:** Even with a fast model, the total round-trip time (User Speech -> VAD -> BE -> AI -> BE -> TTS -> User Hears) might feel sluggish, breaking the illusion of a real-time conversation. | **Optimize the "Time to First Sound":** Prioritize streaming the very first chunk of audio from the AI back to the user as quickly as possible. Provide immediate visual feedback in the HUD (e.g., a "thinking" animation) the moment the user stops speaking. |

