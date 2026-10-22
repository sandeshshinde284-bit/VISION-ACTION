import { ref, onMounted, computed } from 'vue';
import { container } from '@/core/di.container';

// Declare SHARED, GLOBAL states outside the function block!
// In Vue 3, this turns the composable into a global state manager (Singleton)
const connectionStatus = ref('Disconnected');
const aiState = ref<'STANDBY' | 'THINKING' | 'STREAMING' | 'SPEAKING'>('STANDBY');
const isCancelled = ref(false); // Set true when user clicks Cancel; discards the in-flight response
const agentStatus = ref<string>('V.I.S.I.O.N. is thinking...');
const receivedMessages = ref<string[]>([]);
const lastSessionId = ref('default_session');
const lastAdminName = ref('');
const isIntentionalDisconnect = ref(false);
const activeSessionTitle = ref('');

let isInitialized = false;
let thinkingStartTime = 0;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null; // Background reconnection timer task
let currentStreamingMessage = ''; // Accumulate streaming chunks into a single message
let streamingMessageIndex = -1; // Track which message array index is currently streaming
const webSocketService = container.webSocketService;

export function useWebSocket() {
  const isConnected = computed(() => connectionStatus.value === 'Connected')

  const triggerAutoReconnect = () => {
    if (reconnectTimeout) clearTimeout(reconnectTimeout);

    // Automatically wait 3 seconds, then attempt to reconnect silently in the background
    reconnectTimeout = setTimeout(() => {
      // log: "V.I.S.I.O.N. Link offline. Attempting automatic background reconnection...");
      connectionStatus.value = 'Reconnecting...';
      isInitialized = false; // Release lock so connect() can instantiate socket
      connect(lastSessionId.value, lastAdminName.value);
    }, 3000);
  };

  const connect = (sessionId: string = 'default_session', adminName: string = '') => {
    isIntentionalDisconnect.value = false; // Reset intentional lock on connection
    // Only connect if we haven't initialized the socket yet!
    if (isInitialized) return;
    isInitialized = true;

    if (!adminName) {
      adminName = sessionStorage.getItem('vision_admin_name') || 'Administrator';
    }

    // Cache parameters for background automatic reconnects
    lastSessionId.value = sessionId;
    lastAdminName.value = adminName;

    connectionStatus.value = 'Connecting...';

    webSocketService.connect(
      () => {
        connectionStatus.value = 'Connected';
        // Connection Succeeded! Cancel any active background reconnection tasks immediately
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      },
      (data) => {
        // Filter 1: Intercept real-time backend agent status packets on-the-fly!
        if (data.startsWith('[SYSTEM_STATUS:')) {
          const match = data.match(/\[SYSTEM_STATUS:\s*(.*?)\]/i);
          if (match && match[1]) {
            agentStatus.value = match[1].trim();
          }
          return; // Do not append to chat!
        }

        // Filter 2: Intercept session rename system notifications
        if (data.startsWith('[SYSTEM_SESSION_RENAME:')) {
          // Parse and handle session rename silently
          const match = data.match(/\[SYSTEM_SESSION_RENAME:\s*(.*?):(.*?)\]/i);
          if (match && match[2]) {
            // Session was renamed to match[2]
            // log: "Session renamed to:", match[2]);
            activeSessionTitle.value = match[2];
          }
          return; // Do not append to chat!
        }

        // Filter 3: Filter out any other system messages that shouldn't be displayed
        if (data.startsWith('[SYSTEM:') || data.includes('[SYSTEM ')) {
          return; // Do not append to chat!
        }

        // --- STEP 4 OPTIMIZATION: PARSE STRUCTURED JSON FRAMES ---
        try {
          const frame = JSON.parse(data);

          if (frame.type === 'message_start') {
            // New stream started! Reset accumulator indices
            currentStreamingMessage = '';
            streamingMessageIndex = -1;
            return;
          }

          if (frame.type === 'system_status') {
            // Structured status indicator frame
            agentStatus.value = frame.status || '';
            return; // Do not append to chat!
          }

          if (frame.type === 'text_chunk') {
            // ISSUE #8 fix: once the first token arrives, move out of THINKING into
            // STREAMING so the UI can show "responding..." instead of leaving the
            // "thinking" indicator showing while text is already visible.
            if (isCancelled.value) {
              return; // User cancelled this request - drop incoming chunks silently
            }
            if (aiState.value === 'THINKING') {
              aiState.value = 'STREAMING';
            }

            const chunkContent = frame.content || '';
            currentStreamingMessage += chunkContent;

            if (streamingMessageIndex < 0) {
              receivedMessages.value.push(currentStreamingMessage);
              streamingMessageIndex = receivedMessages.value.length - 1;
            } else {
              // Update existing message reactively (Vue will re-render)
              receivedMessages.value[streamingMessageIndex] = currentStreamingMessage;
            }
            return;
          }

          if (frame.type === 'smart_action') {
            // Append structured tag into text stream. Parsed on render in SystemLog.vue!
            const payloadStr = JSON.stringify(frame.payload);
            const actionTag = `\n\n[SMART_ACTION:${payloadStr}]`;
            
            if (streamingMessageIndex >= 0) {
              receivedMessages.value[streamingMessageIndex] += actionTag;
            } else {
              receivedMessages.value.push(actionTag);
            }
            return;
          }

          if (frame.type === 'ambiguous_intent') {
            // Append structured tag into text stream. Parsed on render in SystemLog.vue!
            const payloadStr = JSON.stringify(frame.payload);
            const actionTag = `\n\n[AMBIGUOUS_INTENT:${payloadStr}]`;
            
            if (streamingMessageIndex >= 0) {
              receivedMessages.value[streamingMessageIndex] += actionTag;
            } else {
              receivedMessages.value.push(actionTag);
            }
            return;
          }

          if (frame.type === 'streaming_complete') {
            // Close stream and reset index
            streamingMessageIndex = -1;
            currentStreamingMessage = '';
            agentStatus.value = 'V.I.S.I.O.N. is thinking...'; // Reset for next query
            aiState.value = 'STANDBY';
            isCancelled.value = false; // Clear cancel flag now that this request is done
            return;
          }

        } catch {
          // Fallback if data is not JSON (legacy support)
          // warn: "WebSocket received non-JSON frame, falling back to legacy parsing:", data);
          
          if (isCancelled.value) {
            return; // User cancelled this request - drop legacy frames silently too
          }

          const isEndMarker = data.includes('[SOURCE:') ||
                             data.includes('[TOKENS:') ||
                             data.includes('[ADO_COUNT:');

          if (isEndMarker) {
            currentStreamingMessage += data;
            if (currentStreamingMessage.length > 0) {
              if (streamingMessageIndex >= 0) {
                receivedMessages.value[streamingMessageIndex] = currentStreamingMessage;
              } else {
                receivedMessages.value.push(currentStreamingMessage);
              }
              streamingMessageIndex = -1;
              currentStreamingMessage = '';
            }
            agentStatus.value = 'V.I.S.I.O.N. is thinking...';
            aiState.value = 'STANDBY';
            isCancelled.value = false;
          } else {
            if (aiState.value === 'THINKING') {
              aiState.value = 'STREAMING';
            }
            currentStreamingMessage += data;
            if (streamingMessageIndex < 0) {
              receivedMessages.value.push(currentStreamingMessage);
              streamingMessageIndex = receivedMessages.value.length - 1;
            } else {
              receivedMessages.value[streamingMessageIndex] = currentStreamingMessage;
            }
          }
        }
      },
      () => {
        connectionStatus.value = 'Disconnected';
        isInitialized = false;
        // Reset streaming state on disconnect
        currentStreamingMessage = '';
        streamingMessageIndex = -1;
        // Only trigger auto-reconnect if the disconnection was ACCIDENTAL!
        if (!isIntentionalDisconnect.value) {
          triggerAutoReconnect();
        }
      },
      () => {
        connectionStatus.value = 'Error';
        isInitialized = false;
        // Reset streaming state on error
        currentStreamingMessage = '';
        streamingMessageIndex = -1;
        // Only trigger auto-reconnect if the disconnection was ACCIDENTAL!
        if (!isIntentionalDisconnect.value) {
          triggerAutoReconnect();
        }
      },
      (state) => {
        if (state === 'THINKING') {
          thinkingStartTime = Date.now();
          isCancelled.value = false; // Fresh request - clear any stale cancel flag
          aiState.value = state;
        } else {
          const timeSpentThinking = Date.now() - thinkingStartTime;
          const remainingTime = (aiState.value === 'THINKING') ? Math.max(0, 800 - timeSpentThinking) : 0;
          setTimeout(() => {
            aiState.value = state;
          }, remainingTime);
        }
      },
      sessionId,
      adminName
    );
  };

  const sendMessage = (message: string) => {
    // Reset streaming state when sending new message
    currentStreamingMessage = '';
    streamingMessageIndex = -1;
    webSocketService.sendMessage(message);
  };

  const interruptAudio = () => {
    webSocketService.interruptAudio();
  };

  // ISSUE #9 fix: lets the user bail out of a stuck/slow request.
  // This is a "soft" cancel - the backend request already in flight (running in a
  // thread executor) keeps running to completion, but the frontend immediately
  // stops showing "thinking"/"streaming" and discards whatever response eventually
  // arrives for it, so the user isn't stuck staring at a frozen indicator.
  const cancelRequest = () => {
    isCancelled.value = true;
    currentStreamingMessage = '';
    streamingMessageIndex = -1;
    agentStatus.value = 'V.I.S.I.O.N. is thinking...';
    aiState.value = 'STANDBY';
    receivedMessages.value.push('[SYSTEM: Request cancelled by user]');
  };

  const disconnect = () => {
    isIntentionalDisconnect.value = true; // Lock accidental reconnects
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    // Reset streaming state
    currentStreamingMessage = '';
    streamingMessageIndex = -1;
    webSocketService.disconnect();
    isInitialized = false;
    connectionStatus.value = 'Disconnected';
  };

  const sendAudioData = (audioBlob: Blob) => {
    // Reset streaming state when sending new audio
    currentStreamingMessage = '';
    streamingMessageIndex = -1;
    if(isConnected.value){
      webSocketService.sendAudio(audioBlob);
      receivedMessages.value.push("[Audio data to server....]");
    }
  };

  // Connect once when the first component mounts
  onMounted(() => {
    connect(lastSessionId.value, lastAdminName.value);
  });

  // DO NOT DISCONNECT ON UNMOUNT anymore!
  // Removing webSocketService.disconnect() from onUnmounted prevents the 
  // AudioRecorder unmounting from killing the active connection!

  return {
    connectionStatus,
    aiState,
    agentStatus, // Exported real-time status updates!
    activeSessionTitle, // Exported for auto-title UI updates!
    receivedMessages,
    sendMessage,
    interruptAudio,
    cancelRequest,
    connect,
    disconnect,
    sendAudioData,
    isConnected
  };
}
