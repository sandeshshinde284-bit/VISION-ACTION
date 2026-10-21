# V.I.S.I.O.N. System Instructions & Documentation Mandates

Welcome, Assistant. This document defines strict, mandatory rules for codebase management, documentation synchronization, and educational tracking inside the **V.I.S.I.O.N. Suite**.

You must read and adhere to these guidelines during every single session.

---

## 1. Documentation Auto-Update Mandate (CRITICAL)
Whenever you modify, add, or delete any code, visual layout, or backend functionality, you **MUST** immediately update the corresponding documentation files in tandem:

1.  **Functional Changes / Features / Deliverables**: 
    - Update **`docs/07-FunctionalRequirements.md`**. Ensure the Milestone Tracker (TODO lists) and Feature Specifications perfectly reflect the active state of the application.
2.  **Architecture / Data Sockets / Infrastructure**:
    - Update **`docs/08-Architecture.md`**. Keep the system maps, data schemas, Zscaler bypasses, and communication states current.
3.  **AI Engine / Prompts / RAG Rules**:
    - Update **`docs/09-AIEngine.md`**. Document all models used, prompt persona details, and vector indexing specifications.
4.  **Installation & Execution (Runbook)**:
    - Update **`docs/04-Runbook.md`**. Ensure the dependencies list, environment variables (`.env`), first-time setup, and run commands are kept perfectly up-to-date.

---

## 2. Technical Learning & Curriculum Mandate
Sandesh (the Administrator) uses this project as a study environment to master modern software engineering and AI architectures. 

Whenever you introduce a new technology, framework, Python library, or design pattern:
*   You **MUST** document it inside **`docs/10-LearningGuide.md`**.
*   Structure the entry into three parts:
    1.  **What is it?** (Simple explanation).
    2.  **Why did we use it?** (How it solves our Magellon use-case).
    3.  **How does it work?** (Code examples and operational flow).

---

## 3. Local Sandbox Rules
- Maintain strict local boundaries. Do not push raw data or company Confluence/ADO payloads into public cloud environments.
- Enforce the **`gemini-2.5-flash`** model on the backend for standard operations, allowing fallback to Pro only when requested by the Administrator.
