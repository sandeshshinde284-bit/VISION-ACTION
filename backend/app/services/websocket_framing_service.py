import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebSocketFramingService:
    """
    Phase 4: Option C++ WebSocket Framing Service.
    Surgically serializes and wraps all streaming chunks, smart buttons, 
    and intent clarification prompts into strict JSON frames.
    """
    
    def build_message_start(self, message_id: str) -> str:
        return json.dumps({
            "type": "message_start",
            "id": message_id,
            "is_streaming": True
        })
        
    def build_text_chunk(self, message_id: str, content: str) -> str:
        return json.dumps({
            "type": "text_chunk",
            "id": message_id,
            "content": content
        })
        
    def build_smart_action(self, message_id: str, keyword: str) -> str:
        return json.dumps({
            "type": "smart_action",
            "id": message_id,
            "payload": {
                "action_type": "SINGLE_BUTTON",
                "keyword": keyword,
                "label": "🎫 Fetch Live Tickets"
            }
        })
        
    def build_ambiguous_intent(self, message_id: str, payload_data: dict) -> str:
        # Override payload's temporary message_id with the active conversation message_id
        payload_copy = dict(payload_data)
        payload_copy["message_id"] = message_id
        
        return json.dumps({
            "type": "ambiguous_intent",
            "id": message_id,
            "payload": payload_copy
        })
        
    def build_streaming_complete(self, message_id: str) -> str:
        return json.dumps({
            "type": "streaming_complete",
            "id": message_id
        })
        
    def build_system_status(self, message_id: str, status_text: str) -> str:
        """Emit a structured system status update (e.g., 'Analyzing intent...')"""
        return json.dumps({
            "type": "system_status",
            "id": message_id,
            "status": status_text
        })

# Singleton
websocket_framer = WebSocketFramingService()
