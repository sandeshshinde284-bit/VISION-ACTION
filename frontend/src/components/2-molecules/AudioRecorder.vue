<!-- /frontend/src/components/2-molecules/AudioRecorder.vue -->
<template>
  <section class="flex flex-col items-center justify-center space-y-4">
    
    <!-- vision CORE -->
    <visionCore 
      :state="currentVisualState"
      @click="toggleSession"
    />

    <!-- CORE SYSTEM STATE LABELS (DYNAMIC GLOWS) -->
    <div class="text-[10px] md:text-[11px] font-black uppercase tracking-[0.3em] h-6 flex items-center select-none">
      <span v-if="currentVisualState === 'LISTENING'" class="text-red-500 animate-pulse drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]">
        Listening...
      </span>
      <span v-else-if="currentVisualState === 'THINKING'" class="text-[var(--accent)] animate-pulse drop-shadow-[0_0_8px_var(--accent)]">
        Processing...
      </span>
      <span v-else-if="currentVisualState === 'SPEAKING'" class="text-[var(--accent)] drop-shadow-[0_0_8px_var(--accent)] flex items-center space-x-1.5">
        <span class="inline-block w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-ping"></span>
        <span>Transmitting...</span>
      </span>
      <span v-else class="text-slate-500 opacity-60">
        <!-- Standby remains blank and clean, removing sci-fi clutter -->
      </span>
    </div>

  </section>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import visionCore from '@/components/2-molecules/visionCore.vue';
import { useWebSocket } from '@/composables/useWebSocket';

const props = defineProps<{
  isConnected: boolean;
  aiState: 'STANDBY' | 'THINKING' | 'SPEAKING';
}>();

const emit = defineEmits<{
  (e: 'audio-recorded', data: Blob): void;
  (e: 'listening-start'): void;
  (e: 'listening-stop'): void;
}>();

const { interruptAudio, sendMessage } = useWebSocket();

// --- Reactive State ---
const isSessionActive = ref(false);
const isVoiceDetected = ref(false);

// Audio Refs
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];
let audioContext: AudioContext | null = null;
let analyser: AnalyserNode | null = null;
let microphoneSource: MediaStreamAudioSourceNode | null = null;
let animationFrameId: number | null = null;
let activeStream: MediaStream | null = null;

const VOLUME_THRESHOLD = 50; 
const SILENCE_DURATION = 1500;
let lastSpeechTime = 0;

const currentVisualState = computed(() => {
  if (isVoiceDetected.value) return 'LISTENING';
  return props.aiState;
});

const toggleSession = async () => {
  if (isSessionActive.value) {
    stopSession();
    sendMessage("[SYSTEM: User terminated the voice session]");
  } else {
    await startSession();
    sendMessage("[SYSTEM: User established a new voice session]");
  }
};

const startSession = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
    });
    activeStream = stream;
    isSessionActive.value = true;

    audioContext = new AudioContext();
    analyser = audioContext.createAnalyser();
    microphoneSource = audioContext.createMediaStreamSource(stream);
    microphoneSource.connect(analyser);
    analyser.fftSize = 256;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      if (audioChunks.length > 0) {
        emit('audio-recorded', new Blob(audioChunks, { type: 'audio/webm' }));
        audioChunks = [];
      }
    };

    const checkVolume = () => {
      if (!isSessionActive.value) return;
      analyser?.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) sum += dataArray[i] ?? 0;
      const averageVolume = sum / dataArray.length;
      const currentTime = Date.now();

      if (averageVolume > VOLUME_THRESHOLD) {
        if (!isVoiceDetected.value) {
          interruptAudio();
          isVoiceDetected.value = true;
          emit('listening-start');
          mediaRecorder?.start();
        }
        lastSpeechTime = currentTime;
      } else if (isVoiceDetected.value && (currentTime - lastSpeechTime > SILENCE_DURATION)) {
        isVoiceDetected.value = false;
        emit('listening-stop');
        mediaRecorder?.stop();
      }
      animationFrameId = requestAnimationFrame(checkVolume);
    };
    checkVolume();
  } catch (err) {
    // error: "VAD Error:", err);
  }
};

const stopSession = () => {
  isSessionActive.value = false;
  isVoiceDetected.value = false;
  emit('listening-stop');
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop();
  if (audioContext) audioContext.close();
  if (activeStream) activeStream.getTracks().forEach(track => track.stop());
};

onUnmounted(() => stopSession());

// EXPOSE FOR PARENT CONTROL
defineExpose({
  isSessionActive,
  toggleSession
});
</script>
