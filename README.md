# J.A.R.V.I.S. (Autonomous Technical Assistant)

A professional, voice-first HUD (Heads-Up Display) designed for advanced system orchestration and technical assistance.

## Core Features
- **High-Precision HUD**: A technical interface with real-time state visualization (Listening, Thinking, Speaking).
- **Multimodal Brain**: Powered by Google Cloud Vertex AI (Gemini 2.5 Flash), supporting both voice and text inputs.
- **Real-time Diagnostics**: Direct hardware monitoring (CPU, RAM, Disk) streamed via WebSockets.
- **Enterprise Security**: Compliant with Identity-Based Authentication (ADC) and corporate proxy-aware SSL handling.
- **Hybrid Tool-Belt**: Integrated access to local system tools and real-time internet search.

## Technology Stack
- **Frontend**: Vue 3, TypeScript, Tailwind CSS (Glassmorphism & Complex Animations).
- **Backend**: Python 3.12+, FastAPI, Uvicorn, psutil.
- **AI Infrastructure**: Google Cloud Platform (Vertex AI SDK).

## Documentation
Detailed architectural and operational documents can be found in the `/docs` directory.
- [Setup & Runbook](./docs/04-Runbook.md)
- [System Architecture & Flow](./docs/06-SystemFlow.md)
- [Protocol Specification](./docs/03-ProtocolSpec.md)
