# ADR 003: Choice of Web Audio Format

**Status:** Accepted
**Date:** 2024-05-29

## Context
The frontend needs to capture audio and send it to the backend for AI processing. We need to choose a format that is well-supported by browsers and suitable for AI models.

## Decision
We will use the default format provided by the `MediaRecorder` API, which is typically **`audio/webm` encoded with the Opus codec**.

## Consequences
*   **Pros:**
    *   `webm/opus` is a modern, high-quality, high-compression format. It results in smaller file sizes, reducing network latency.
    *   It is the standard default for `MediaRecorder` in Chrome and Firefox, requiring no special configuration.
    *   The Gemini API can directly process this format.
*   **Cons:**
    *   The backend will need to be capable of handling raw binary data (`bytes`) instead of just text. This requires updating our WebSocket endpoint.