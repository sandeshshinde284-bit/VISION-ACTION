import logging
import json
import uuid
from typing import Dict, Any, List
from vertexai.preview.generative_models import Content, Part

logger = logging.getLogger(__name__)

class IntentClassifierService:
    """
    Phase 4: Option C++ Semantic Intent Classifier.
    Decoupled service to mathematically evaluate and route user queries to prevent hallucination.
    """
    
    def classify(self, user_query: str, history_list: list, ai_service_ref) -> Dict[str, Any]:
        """
        Queries the Utility LLM for raw intent scores, then applies the strict decision tree.
        """
        if not ai_service_ref.utility_model:
            logger.warning("Utility model offline for Intent Classification. Defaulting to INTERNAL.")
            return self._build_result("INTERNAL", 1.0, {}, "Utility model offline fallback.")
            
        prompt = (
            "You are a strict, highly accurate intent classifier for an enterprise AI assistant. "
            "Analyze the user's latest query and the conversation history. "
            "Score the probability of the user's intent across these 4 categories on a scale of 0.00 to 1.00:\n\n"
            "1. EXPLICIT_ADO: The user is explicitly asking to see, fetch, pull, or check live Azure DevOps tickets, bugs, or work items.\n"
            "2. CHAT: Conversational filler, greetings, thanks, approvals (e.g., 'yes', 'ok'), or simple acknowledgments.\n"
            "3. INTERNAL: Asking about theoretical architecture, documentation, how things work, or specifications.\n"
            "4. WEB: General knowledge outside the scope of internal Magellon projects, requiring a public internet search.\n\n"
            "Return ONLY a valid JSON block matching this exact structure, with no markdown formatting:\n"
            "{\n"
            '  "scores": {"EXPLICIT_ADO": 0.0, "CHAT": 0.0, "INTERNAL": 0.0, "WEB": 0.0},\n'
            '  "reason": "Brief 1-sentence explanation of scores"\n'
            "}"
        )

        try:
            # Build history context
            context_payload = list(history_list)
            from vertexai.generative_models import Content, Part
            context_payload.append(Content(
                role="user", 
                parts=[Part.from_text(f"[INTENT CLASSIFICATION TASK]\nUser Query: {user_query}\n\n{prompt}")]
            ))

            # Query the fast, robotic utility model
            response = ai_service_ref._generate_with_retry(context_payload, model_override=ai_service_ref.utility_model)
            raw_json = ai_service_ref._extract_safe_text(response)
            
            # Clean up JSON if LLM added markdown backticks
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:]
            if raw_json.startswith("```"):
                raw_json = raw_json[3:]
            if raw_json.endswith("```"):
                raw_json = raw_json[:-3]
                
            data = json.loads(raw_json.strip())
            scores = data.get("scores", {})

            if not scores or sum(scores.values()) == 0:
                logger.warning(f"Invalid scores from LLM: {scores}. Using fallback.")
                return self._build_result("INTERNAL", 1.0, {}, "LLM returned invalid scores.")

            reason = data.get("reason", "No reason provided")
            
            # Pass raw scores into the strict decision tree
            return self._apply_decision_tree(scores, reason)
            
        except Exception as e:
            logger.warning(f"Intent Classification failed: {e}. Defaulting to INTERNAL.")
            return self._build_result("INTERNAL", 1.0, {}, "Fallback due to classification failure.")

    def _apply_decision_tree(self, scores: Dict[str, float], reason: str) -> Dict[str, Any]:
        """ Executes the mathematical decision tree defined in the Phase 4 blueprint. """
        # Ensure all keys exist
        ado_score = float(scores.get("EXPLICIT_ADO", 0.0))
        chat_score = float(scores.get("CHAT", 0.0))
        int_score = float(scores.get("INTERNAL", 0.0))
        web_score = float(scores.get("WEB", 0.0))
        
        # 1. High-Priority Overrides
        if ado_score >= 0.85:
            logger.info(f"Decision Tree: EXPLICIT_ADO (score={ado_score:.2f} >= 0.85 threshold)")
            return self._build_result("EXPLICIT_ADO", ado_score, scores, reason)
            
        if chat_score >= 0.80:
            logger.info(f"Decision Tree: CHAT (score={chat_score:.2f} >= 0.80 threshold)")
            return self._build_result("CHAT", chat_score, scores, reason)
            
        # 2. Sort remaining scores to find top and runner-up
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_intent, top_score = sorted_scores[0]
        runner_up_intent, runner_up_score = sorted_scores[1]
        
        # 3. Confidence and Margin Check (Tie-breaking rule)
        if top_score >= 0.75 and (top_score - runner_up_score) > 0.10:
            return self._build_result(top_intent, top_score, scores, reason)
            
        # 4. Fallback: AMBIGUOUS
        return self._build_ambiguous(top_score, scores, reason, top_intent, runner_up_intent)
        
    def _build_result(self, intent: str, confidence: float, scores: dict, reason: str) -> Dict[str, Any]:
        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "scores": scores,
            "reason": reason
        }
        
    def _build_ambiguous(self, top_score: float, scores: dict, reason: str, intent1: str, intent2: str) -> Dict[str, Any]:
        """Constructs the structured JSON payload for Vue to render the AmbiguousPrompt component."""
        
        # Helper to map intent to user-friendly UX labels
        labels = {
            "INTERNAL": {"label": "📚 Architecture/Docs", "desc": "Internal system specifications"},
            "EXPLICIT_ADO": {"label": "🎫 Live Tickets", "desc": "Active Azure DevOps work items"},
            "WEB": {"label": "🌐 Web Search", "desc": "General knowledge from the internet"},
            "CHAT": {"label": "💬 Chat", "desc": "General conversation"}
        }
        
        opt1 = labels.get(intent1, {"label": intent1, "desc": "Option A"})
        opt2 = labels.get(intent2, {"label": intent2, "desc": "Option B"})
        
        return {
            "intent": "AMBIGUOUS",
            "confidence": round(top_score, 4),
            "scores": scores,
            "reason": reason,
            "payload": {
                "type": "ambiguous_intent",
                "message_id": f"msg_{uuid.uuid4().hex[:8]}", # NOTE: This message_id is temporary and will be overridden by WebSocket framing layer, # (STEP 4 responsibility). It serves as a placeholder for frontend component rendering.
                "confidence": round(top_score, 4),
                "reason": reason,
                "options": [
                    { "intent": intent1, "label": opt1["label"], "description": opt1["desc"] },
                    { "intent": intent2, "label": opt2["label"], "description": opt2["desc"] }
                ]
            }
        }

# Singleton
intent_classifier = IntentClassifierService()
