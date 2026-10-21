# ADR 001: Choice of Core Frameworks (FastAPI and Vue.js)

**Status:** Accepted
**Date:** 2023-10-26

## Context

The project requires a web-based frontend for user interaction and a backend to orchestrate AI models and business logic. The backend needs to handle real-time, persistent connections for audio streaming.

## Decision

We will use:
1.  **FastAPI (Python)** for the backend.
2.  **Vue.js 3** for the frontend.

## Consequences

*   **Pros:**
    *   Python has a mature AI/ML ecosystem (Google SDK, etc.).
    *   FastAPI has native support for `async` and WebSockets, which is critical for our real-time needs.
    *   Vue 3 is a modern, reactive framework that is performant and easy to learn. The Vite build tool offers a superior developer experience.
*   **Cons:**
    *   Python's GIL can be a concern for CPU-bound tasks, but our application is I/O-bound (waiting for network/AI), making `async` a perfect fit.