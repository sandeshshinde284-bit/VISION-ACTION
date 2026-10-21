import type { IWebSocketService, MessageCallback, EventCallback, StateCallback } from '@/core/services/IWebSocketService';

export class WebSocketService implements IWebSocketService {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private onStateChange: StateCallback | null = null;
  private isVoiceActive: boolean = false; // Tracks whether current session should play voice outputs

  constructor() {
    // ------------------------------------------------------------
    // UNIFIED RELATIVE AGILE ROUTING (PHASE 4)
    // ------------------------------------------------------------
    // For local dev, Vite connects directly to 127.0.0.1:8000. 
    const isLocal = window.location.href.indexOf('localhost') > -1 || window.location.href.indexOf('127.0.0.1') > -1;

    if (isLocal) {      this.url = "ws://127.0.0.1:8000/ws/audio";
    } else {
      // In cloud, use secure WebSockets relative to the active GCP Custom Domain
      this.url = `wss://${window.location.host}/ws/audio`;
    }
  }

  connect(
    onOpen: EventCallback,
    onMessage: MessageCallback,
    onClose: EventCallback,
    onError: EventCallback,
    onStateChange?: StateCallback,
    sessionId: string = 'default_session',
    adminName: string = ''
  ): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    if (onStateChange) this.onStateChange = onStateChange;

    if (!adminName) {
        adminName = sessionStorage.getItem('vision_admin_name') || 'Administrator';
    }

    // Dynamically build WS parameterized handshake URL
    const connUrl = `${this.url}?session_id=${encodeURIComponent(sessionId)}&admin_name=${encodeURIComponent(adminName)}`;
    this.socket = new WebSocket(connUrl);
    this.socket.binaryType = 'blob'; // Ensure binary data is received as Blobs

    this.socket.onopen = () => {
      onOpen();
    };

    this.socket.onmessage = (event) => {
      // 1. Silent processing (Raw metadata logs stripped from browser console - Phase 4)

      // 2. We check if the message is 'binary' (like an image or audio file).
      if (event.data instanceof Blob) {
        onMessage("[Binary data received - currently unsupported]");
      } else {
        // 3. Handle Text/JSON message
        const text = event.data;

        // Defensive Client-Side Guardrail: Block/ignore any incoming telemetry or metadata frames
        try {
          const parsed = JSON.parse(text);
          if (parsed.type === 'telemetry') {
            return; // Silently abort processing and ignore telemetry frames
          }
        } catch {
          // Not JSON, continue to render as regular message
        }

        // 4. Update the UI log so the user can see the text.
        onMessage(text);

        // 5. 'TEXT-TO-SPEECH' (TTS)
        // We only speak if a voice session is active AND the message is NOT a technical error.
        const isError = text.includes("Diagnostic failure") || 
                        text.includes("error:") || 
                        text.includes("Encountered an error");

        if ('speechSynthesis' in window && !isError && this.isVoiceActive) {
          const utterance = new SpeechSynthesisUtterance(text);
          
          // Emit SPEAKING state
          if (this.onStateChange) this.onStateChange('SPEAKING');

          // --- ROBUST VOICE SELECTION ---
          const setVoice = () => {
            const voices = window.speechSynthesis.getVoices();
            // Look for a British Male voice (J.A.R.V.I.S. style)
            const visionVoice = voices.find(v => 
              v.name.includes('Google UK English Male') || 
              v.name.includes('Microsoft George') || 
              v.lang === 'en-GB'
            );
            
            if (visionVoice) utterance.voice = visionVoice;
            utterance.pitch = 0.85; 
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
          };

          // Browsers load voices asynchronously. If they aren't ready, wait for them.
          if (window.speechSynthesis.getVoices().length === 0) {
            window.speechSynthesis.onvoiceschanged = setVoice;
          } else {
            setVoice();
          }
          
          utterance.onend = () => {
            // Return to STANDBY when finished speaking
            if (this.onStateChange) this.onStateChange('STANDBY');
          };
        }
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket connection closed.");
      this.socket = null;
      onClose();
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error: ", error);
      onError();
    };
  }

  sendMessage(message: string): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.isVoiceActive = false; // Typed message -> Silence voice feedback
      // Set UI to THINKING when a text command is sent
      if (this.onStateChange) this.onStateChange('THINKING');
      this.socket.send(message);
    } else {
      console.error("Cannot send message: WebSocket is not connected.");
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

sendAudio(data: Blob): void {
  if(this.socket?.readyState === WebSocket.OPEN) {
    this.isVoiceActive = true; // Spoken message -> Enable voice feedback
    if (this.onStateChange) this.onStateChange('THINKING');
    this.socket.send(data);
  } else {
    console.error("Cannot send audio: WebSocket is not connected.");
  }
}

interruptAudio(): void {
  console.log("Interrupting J.A.R.V.I.S. audio output...");
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    if (this.onStateChange) this.onStateChange('STANDBY');
  }
}

}
