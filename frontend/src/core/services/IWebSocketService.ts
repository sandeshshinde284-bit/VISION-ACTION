export type MessageCallback = (data: string) => void;
export type EventCallback = () => void;
export type StateCallback = (state: 'THINKING' | 'SPEAKING' | 'STANDBY') => void;

export interface IWebSocketService {
  connect(
    onOpen: EventCallback,
    onMessage: MessageCallback,
    onClose: EventCallback,
    onError: EventCallback,
    onStateChange?: StateCallback,
    sessionId?: string,
    adminName?: string
  ): void;
  sendMessage(message: string): void;
  disconnect(): void;

  sendAudio(data: Blob): void;
  interruptAudio(): void;
}
