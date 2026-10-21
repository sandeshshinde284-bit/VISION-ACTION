import { WebSocketService } from '@/infrastructure/services/WebSocketService';
import type { IWebSocketService } from '@/core/services/IWebSocketService';

/**
 * Dependency Injection Container
 *
 * In a larger application, this might be a more complex system (like InversifyJS).
 * For now, we manually instantiate and export our services to maintain the DI pattern.
 */
class DIContainer {
  private _webSocketService: IWebSocketService | null = null;

  get webSocketService(): IWebSocketService {
    this._webSocketService ??= new WebSocketService();
    return this._webSocketService;
  }
}

export const container = new DIContainer();
