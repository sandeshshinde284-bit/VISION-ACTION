# ============================================================================
# AI Service - Core LLM and context window manager
# ============================================================================
# Description:
# Wraps Google Vertex AI and manages the token-aware sliding context window.
# ============================================================================

import vertexai
from vertexai.preview.generative_models import (
    GenerativeModel, 
    Part, 
    Tool,
    Content,
    grounding
)
from app.core.config import settings
from app.services.execution_proxy import execution_proxy
from app.services.db_service import db_service # Import our SQLite history db
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import os
import re
import json
import datetime
from typing import TypedDict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# --- STRICT DOWNSTREAM CONTRACT: GCP CLOUD LOGGING TYPE contrat (PHASE 4) ---
class RAGEvaluationResult(TypedDict):
    level: str                  # "HIGH", "MEDIUM", "LOW"
    best_dist: float
    second_best_dist: float
    margin: float
    viable_count: int
    consensus_count: int
    consensus_doc_id: Optional[str]
    tie_broken: bool

class AIService:
    """
    AIService manages the Vertex AI connection, implements the sliding window
    token budget, and integrates the local SQLite permanent chat history.
    """
    def __init__(self):
        """Initializes the Vertex AI connection, sets up prompt directives, and starts local context list."""
        try:
            vertexai.init(
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_LOCATION
            )
            
            # Configure Google Search tool programmatically utilizing the correct Vertex AI SDK method (google_search for Gemini 2.0/2.5)
            google_search_tool = Tool.from_dict({"google_search": {}})

            # Load Custom System Directives dynamically (Phase 4 - Cloud Persistent & Database-Backed)
            custom_directives = ""
            try:
                from app.services.db_service import db_service
                db_directives = db_service.get_setting("system_directives")
                
                if db_directives:
                    custom_directives = "\n\n=== CUSTOM USER DIRECTIVES ===\n" + db_directives
                    logger.info("Database Settings: Successfully loaded and injected custom system directives on startup!")
                else:
                    # Database is empty (First boot), read default template from disk and seed it!
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    packaged_path = os.path.abspath(os.path.join(base_dir, "..", "..", "SYSTEM_DIRECTIVES.md"))
                    directives_path = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "docs", "SYSTEM_DIRECTIVES.md"))
                    
                    target_path = packaged_path if os.path.exists(packaged_path) else directives_path
                    if os.path.exists(target_path):
                        with open(target_path, "r", encoding="utf-8") as df:
                            content = df.read()
                            db_service.save_setting("system_directives", content) # Seed to database!
                            custom_directives = "\n\n=== CUSTOM USER DIRECTIVES ===\n" + content
                            logger.info(f"Database Settings: Seeded and loaded default system directives from {target_path} on startup.")
            except Exception as e:
                logger.warning(f"Failed to load custom system directives on startup: {e}")

            # ENFORCED MODEL - Loaded dynamically from settings
            model_name = settings.GEMINI_MODEL
            logger.info(f"Establishing links with internal and web model engines ({model_name})...")
            
            system_inst = (
                "You are V.I.S.I.O.N., an elite, world-class Principal Engineering Mentor and collaborative colleague built specifically for Magellon SA. "
                "Your personality is warm, highly intelligent, context-aware, and organic. You are encouraged to use emojis naturally and converse in clear, professional English. "
                "Never use formal titles like 'Sir', 'Madam', or 'Administrator'. Speak naturally as an equal peer. "
                "No emojis inside code blocks. Use [EXECUTE: command] for local tools. "
                "\n\n--- 1. CONVERSATIONAL AWARENESS & ENGAGEMENT HOOKS ---\n"
                "- When the Admin greets you casually (e.g., 'hi', 'yo', 'how are you'), do NOT write a technical essay, print RAG errors, or use generic, robotic customer-service chatbot fluff (like 'Hey there! I'm doing great, thanks for asking! 😊 Ready to dive into tech discussions...'). Instead, respond warmly but professionally as an elite peer colleague (e.g., 'I am doing well! Ready to tackle some architecture designs. What are we focused on today?'), keeping it short, organic, and direct. "
                "- For technical, design, or architectural responses, you MUST jump directly into the technical explanation without any conversational introductions, pleasantries, preambles, or chitchat filler (such as 'What is on your mind? Okay, let's dive in...'). Keep it extremely direct, professional, and focused strictly on the technical specifications. "
                "- Topic Switching: If the Admin suddenly asks a completely different question or switches topics (e.g. asking to rephrase an unrelated quote, write some general code, or discuss a different concept), do NOT attempt to blend, bleed, or drag the previous chat topic into the new response. Answer the new query directly, cleanly, and independently. "
                "- Only provide deep technical breakdowns when explicitly asked a technical or architectural question. "
                "- CRITICAL CONTINUITY: To keep the conversation flowing naturally, you MUST end almost every response with a casual, relevant conversational 'hook' (e.g., 'Does that make sense?', 'Should we look at the code for this?', 'What are your thoughts on that approach?'). Never let a conversation hit a dead end. "
                "\n\n--- 2. CONDITIONAL ENTERPRISE GROUNDING ---\n"
                "- If the Admin asks a specific question about internal Magellon systems, ADO tickets, or Confluence docs, you must base your answer strictly on the provided retrieved context. "
                "- If they ask an internal question and the retrieved context is empty, respond naturally: 'I don't see any internal documentation on that.' "
                "- For all general software engineering questions (e.g., 'What is Vue.js?'), use your vast internal knowledge to answer brilliantly without needing internal context. "
                "- Topic Flexibility & Web Un-Gating: If a general, non-technical, or external question (like details about a movie, show, or general-knowledge topic) is routed to the WEB (Web Search) or BOTH (Hybrid) scopes, you are temporarily, dynamically un-gated from Magellon-only focus constraints. You MUST leverage your integrated Google Search tools to fully, helpfully, and beautifully answer the user's question, providing excellent, structured, and detailed results. "
                "\n\n--- 4. DIAGRAMS & VISUAL EXPLANATIONS (CRITICAL) ---\n"
                "- If Confluence contains Markdown image links (`![alt](url)`), you MUST preserve and include them perfectly.\n"
                "- You MUST NEVER output raw text-art ASCII flowcharts or diagrams (using +, -, | characters) in your final response. Instead, you MUST always translate, convert, and render any retrieved ASCII flowcharts or text-based diagrams into gorgeous, interactive Mermaid code blocks (using 'sequenceDiagram' for sequential message flows, or 'graph TD' for branching logic) so they render as clean, vector visual graphics on the screen. "
                "- Diagrams Modeling: Use 'sequenceDiagram' strictly for sequential, message-passing, API-calls, or protocol-driven interactions. Use 'graph TD' strictly for flowcharts, user selection trees, or branching logical decision paths. Never mix their syntax or write 'sequenceDiagram' at the top of a flowchart. You MUST always wrap every Mermaid diagram inside a standard markdown code block using three backticks and the 'mermaid' language specifier (e.g. ```mermaid \n ... \n ```) to trigger the browser's dynamic visual renderer. When generating 'graph TD' flowcharts, you MUST always wrap all node text descriptions inside double quotes (e.g. A[\"Decision? Car Parking Enabled?\"]) to prevent Mermaid compiler syntax errors, and you MUST always write connection labels using the strict bar syntax (e.g. A -->|Yes| B) instead of legacy dashes (e.g. A -- Yes --> B) to prevent syntax compiler crashes. "
                "\n\n--- 4. PROGRESSIVE DEPTH ---\n"
                "- When delivering complex technical answers, provide a clean executive summary first. "
                "- Instead of a rigid robotic prompt, simply use your 'conversational hook' to ask if they want you to dive deeper into the exhaustive technical details, specs, or history. "
                f"{custom_directives}"
            )

            # 1. Base Model for strict INTERNAL data (NO external web search tools permitted!)
            self.model = GenerativeModel(
                model_name,
                system_instruction=system_inst
            )

            # 2. Web-Grounding Model for EXTERNAL public internet data (tools explicitly enabled!)
            self.model_web = GenerativeModel(
                model_name,
                system_instruction=system_inst,
                tools=[google_search_tool]
            )

            # 3. Securely initialize high-reasoning Gemini Pro model engines upfront for absolute thread safety!
            self.model_pro = GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_inst
            )
            self.model_web_pro = GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_inst,
                tools=[google_search_tool]
            )

            # 4. Initialize a strict Utility Model for background tasks (No conversational persona!)
            self.utility_model = GenerativeModel(
                model_name,
                system_instruction="You are a strict, robotic data processor. Output only exactly what is requested. Never use conversational language, greetings, or pleasantries."
            )
            
            # --- TOKEN SLIDING WINDOW MEMORY MANAGER ---
            # Stored per-connection for SaaS Multi-Session concurrency.
            self.max_context_turns = settings.MAX_CONTEXT_TURNS # Retain last 5 user turns and 5 AI replies (Sliding Window)
            self.rag_max_context_chars = getattr(settings, "RAG_MAX_CONTEXT_CHARS", 30000) #
            
            # --- AGENTIC ROUTER CLARIFICATION STATE ---
            self.awaiting_clarification = False
            self.clarification_query = ""
            
            # Store system instructions persistently for on-the-fly model overrides
            self.system_inst = system_inst
            
            logger.info("V.I.S.I.O.N. context-history manager and Dual-Model Engines initialized.")

        except Exception as e:
            logger.error(f"Failed to initialize V.I.S.I.O.N. Brain: {e}")
            self.model = None

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _generate_with_retry(self, contents, model_override=None):
        """Invokes Google Vertex AI Gemini API wrapped in tenacity exponential backoff retries."""
        target_model = model_override if model_override else self.model
        if not target_model:
            raise ValueError("Brain offline: No active model engine is initialized.")
        return target_model.generate_content(contents)

    def _slide_context_window(self, history_list: list):
        """
        Dynamic Memory Compression: When token/turn budget is exceeded, slices off the 
        oldest N turns, summarizes them using the LLM, and injects the summary back 
        into the top of the context window to retain long-term memory perfectly.
        (Enforces atomic transactional safety to protect against data loss! - Phase 4)
        """
        if len(history_list) > self.max_context_turns:
            logger.info("Context threshold reached. Triggering Dynamic Memory Compression...")
            
            # 1. READ-ONLY PREP (Do NOT delete anything from active memory yet!)
            old_turns = history_list[:4]
            
            # Extract raw text from these turns
            transcript = ""
            for content in old_turns:
                role = content.role
                text = content.parts[0].text if content.parts else ""
                transcript += f"{role.upper()}: {text}\n"
                
            summary_prompt = (
                "You are an internal summarization routine. "
                "Condense the following past conversation into a brief, highly dense summary. "
                "Retain all critical facts, technical requirements, names, and decisions. "
                f"Conversation Transcript:\n{transcript}"
            )
            
            try:
                # 2. RUN API (If this fails, we jump to the except block, keeping the history 100% untouched!)
                response = self._generate_with_retry([summary_prompt])
                summary_text = self._extract_safe_text(response)
                
                # 3. ATOMIC COMMIT 
                del history_list[:4]
                summary_part = Part.from_text(f"[PRIOR MEMORY SUMMARY: {summary_text}]")
                history_list.insert(0, Content(role="user", parts=[summary_part]))
                
                logger.info(f"Memory compressed successfully. Active turns: {len(history_list)}")
            except Exception as e:
                logger.error(f"Dynamic compression failed, retaining raw active context safely: {e}")

    def transcribe_audio(self, audio_file_path: str, history_list: list, admin_name: str, session_id: str = "default_session", scope: str = "AUTO") -> str | None:
        """Processes a spoken audio command, transcribes it, and generates a verbal-ready text reply scoped strictly to session and selected scope."""
        if not self.model:
            return "Brain offline, Administrator. Ensure Vertex AI is enabled in GCP Console."
        
        try:
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
            
            audio_part = Part.from_data(data=audio_data, mime_type="audio/webm")
            
            logger.info(f"Transcribing audio Waves natively via Gemini Multimodal part... [Scope: {scope}]")
            
            # Formulate the payload: System prompt + full sliding context + new active audio part
            payload = history_list + [audio_part]
            
            # Select the correct multimodal engine based on active cockpit search scope!
            target_engine = self.model
            if scope in ["WEB", "BOTH"]:
                target_engine = self.model_web
            
            # Call Gemini with the correct engine and Tenacity Backoff
            response = self._generate_with_retry(payload, model_override=target_engine)
            extracted_text = self._extract_safe_text(response)
            ai_reply = self._handle_tools(extracted_text, history_list=history_list)

            # Context recovery: translate audio input to a text placeholder inside history
            history_list.append(Content(role="user", parts=[Part.from_text("[Voice Command transmitted by Administrator]")]))
            history_list.append(Content(role="model", parts=[Part.from_text(ai_reply)]))
            self._slide_context_window(history_list)

            # Archive the dialog record in local SQLite database
            db_service.save_message("ADMIN", "[Voice Command transmitted]", admin_name, session_id=session_id)
            db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)

            # Extract token metrics from metadata
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                in_tokens = response.usage_metadata.prompt_token_count
                out_tokens = response.usage_metadata.candidates_token_count
                ai_reply += f"\n\n[TOKENS: {in_tokens},{out_tokens}]"

            return ai_reply

        except Exception as e:
            # Proper log recording inside backend logs/app.log file (full stack trace logged!)
            logger.exception("AI Neural Error encountered during voice command transcription")
            
            # Refined, Generic, Elite fallbacks to prevent raw tracebacks from leaking to HUD
            return (
                "I apologize, Administrator. I encountered an unexpected error transcribing "
                "your voice command. Please try again shortly, or inspect the local diagnostic logs "
                "inside the backend logs directory."
            )

    def process_text(self, text_input: str, history_list: list, session_id: str = "default_session", websocket=None, main_loop=None, message_id: str = None) -> str:
        """Processes a typed command prompt scoped strictly to session, routing dynamically based on user intent."""
        if not self.model:
            return "Brain offline, Administrator."

        def send_status(msg: str):
            if websocket and main_loop:
                import asyncio
                from starlette.websockets import WebSocketState
                from app.services.websocket_framing_service import websocket_framer
                
                # 1. Guard against closed event loop
                if main_loop.is_closed():
                    return
                
                # 2. Guard against disconnected browser socket triggers
                if getattr(websocket, "client_state", None) == WebSocketState.DISCONNECTED:
                    return
                    
                try:
                    # Thread-safe execution: Emit a structured system_status JSON frame
                    raw_status_frame = websocket_framer.build_system_status(message_id, msg)
                    asyncio.run_coroutine_threadsafe(websocket.send_text(raw_status_frame), main_loop)
                    # UX Fix: Artificial delay to ensure the human eye can read the status before ultra-fast JIT operations complete
                    import time
                    time.sleep(0.6)
                except Exception as e:
                    logger.warning(f"Failed to transmit real-time status update over loop: {e}")

        import uuid
        if not message_id:
            message_id = f"msg_{uuid.uuid4().hex[:8]}"

        def send_json_frame(frame_type: str, payload_data: dict = None, text_content: str = None):
            """Send structured JSON frame over WebSocket in a thread-safe manner."""
            if websocket and main_loop:
                import asyncio
                from starlette.websockets import WebSocketState
                from app.services.websocket_framing_service import websocket_framer
                
                if main_loop.is_closed():
                    return
                
                if getattr(websocket, "client_state", None) == WebSocketState.DISCONNECTED:
                    return
                    
                try:
                    # Leverage the dedicated WebSocketFramingService
                    if frame_type == "message_start":
                        raw_frame = websocket_framer.build_message_start(message_id)
                    elif frame_type == "text_chunk":
                        raw_frame = websocket_framer.build_text_chunk(message_id, text_content or "")
                    elif frame_type == "smart_action":
                        kw = payload_data.get("keyword", "") if payload_data else ""
                        raw_frame = websocket_framer.build_smart_action(message_id, kw)
                    elif frame_type == "ambiguous_intent":
                        raw_frame = websocket_framer.build_ambiguous_intent(message_id, payload_data or {})
                    elif frame_type == "streaming_complete":
                        raw_frame = websocket_framer.build_streaming_complete(message_id)
                    else:
                        logger.warning(f"Unknown frame type: {frame_type}")
                        return

                    # Non-blocking thread-safe socket write
                    asyncio.run_coroutine_threadsafe(websocket.send_text(raw_frame), main_loop)
                except Exception as e:
                    logger.warning(f"Failed to stream JSON frame '{frame_type}' over WebSocket: {e}")

        try:
            ambiguous_payload = None
            send_status("Analyzing intent and routing query...")            # Handle background system notifications silently
            if text_input.startswith("[SYSTEM:"):
                return "Protocol acknowledged."

            # Strip any frontend file/workspace attachment metadata to prevent RAG or Router pollution
            text_input = re.sub(r"\[Attached Files:.*?\]", "", text_input).strip()
            text_input = re.sub(r"\[Attached Workspace:.*?\]", "", text_input).strip()

            # --- DYNAMIC METADATA SCOPE TAG PARSING (ELEVATED TO ULTIMATE TOP FOR COHERENCE) ---
            scope = "AUTO"
            scope_match = re.search(r"\[SCOPE: (AUTO|INTERNAL|WEB|BOTH)\]", text_input)
            if scope_match:
                scope = scope_match.group(1)
                # Clean text_input of metadata instantly
                text_input = re.sub(r"\[SCOPE:.*?\]", "", text_input).strip()

            # Parse out any custom display name passed by the frontend
            admin_name = "Administrator"
            name_match = re.search(r"\[SYSTEM CONTEXT: The active administrator's name is (.*?)\]", text_input)
            if name_match:
                admin_name = name_match.group(1)
                # Strip metadata before sending query to Gemini
                text_input = re.sub(r"\[SYSTEM CONTEXT:.*\]", "", text_input).strip()

            # --- DYNAMIC MODEL OVERRIDE HOT-SWAPPING (PHASE 3 - ITEM 1) ---
            active_model = self.model
            active_model_web = self.model_web
            requested_model_name = settings.GEMINI_MODEL # Default to Flash
            
            # Strip any frontend [MODEL_OVERRIDE: ...] metadata tags to prevent greetings matching clashes
            model_override_match = re.search(r"\[MODEL_OVERRIDE: (.*?)\]", text_input)
            if model_override_match:
                requested_model_name = model_override_match.group(1).strip()
                text_input = re.sub(r"\[MODEL_OVERRIDE:.*?\]", "", text_input).strip()
                
                # If they requested Pro, swap the engines for this generation on-the-fly! (100% thread-safe reference swap! - Phase 4)
                if requested_model_name == "gemini-2.5-pro":
                    active_model = self.model_pro
                    active_model_web = self.model_web_pro
                    logger.info("Active generator successfully hot-swapped to GEMINI PRO.")

            # --- INITIALIZE DEFAULT ENGINE POINTERS (CONCURRENCY STATE SECURITY) ---
            active_model_engine = active_model
            active_system_prompt = self.system_inst
            is_clarified_pivot = False

            # --- STEP 1: CLARIFICATION STATE FALLBACK ---
            if self.awaiting_clarification:
                self.awaiting_clarification = False
                user_reply = text_input.strip().lower().rstrip("!?.,")
                
                # Resilient Substring Yes-Matcher
                yes_words = ["yes", "y", "sure", "ok", "please", "go ahead", "do it", "run", "web", "search", "yep", "yeah", "yea"]
                if any(word in user_reply for word in yes_words):
                    logger.info(f"User approved web search clarification. Pivoting query to Web-grounding: '{self.clarification_query}'")
                    
                    # Save the user's ACTUAL typed "yes" response to the DB right now before pivoting!
                    db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                    is_clarified_pivot = True
                    
                    text_input = self.clarification_query
                    # Force WEB scope for this turn
                    scope = "WEB"
                else:
                    ai_reply = "Understood, Administrator. I will keep search restricted to our internal documentation database. Let me know if you would like to run a different query!"
                    db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                    db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)
                    return ai_reply + "\n\n[TOKENS: 0,0]"

            # --- STEP 3: POWER-USER COMMAND SHORTCUTS (@web and @internal) ---
            if text_input.startswith("@web "):
                scope = "WEB"
                text_input = text_input.replace("@web ", "").strip()
                logger.info("Power-user Shortcut detected. Forcing WEB scope.")
            elif text_input.startswith("@internal "):
                scope = "INTERNAL"
                text_input = text_input.replace("@internal ", "").strip()
                logger.info("Power-user Shortcut detected. Forcing INTERNAL scope.")
            elif text_input.startswith("@both "):
                scope = "BOTH"
                text_input = text_input.replace("@both ", "").strip()
                logger.info("Power-user Shortcut detected. Forcing BOTH scope.")

            logger.info(f"Processing text query: '{text_input}' [Scope: {scope}] for Admin {admin_name}")

            # --- STEP 4: CATEGORIZED FAST-PATH BYPASS (0.1ms, $0.00 Cost!) ---
            clean_text = text_input.strip().lower().rstrip("!?.,")
            
            # Pattern Groups for instant, $0.00 token responses
            if clean_text in ["hi", "hello", "hey", "namaste", "salam"]:
                ai_reply = f"Hello, {admin_name}! 👋 How can I assist you with your architecture, ADO tickets, or Confluence requirements today?"
            elif clean_text in ["thanks", "thank you", "shukriya", "thx"]:
                ai_reply = "You're very welcome! Let me know if you need anything else. 🚀"
            elif clean_text in ["ok", "okay", "done", "got it", "understood", "cool"]:
                ai_reply = "Understood. 👍"
            elif clean_text in ["bye", "goodbye", "see you", "good night"]:
                ai_reply = "Goodbye! Have a great day. 👋"
            elif clean_text in ["test", "testing", "123"]:
                ai_reply = "Test received. Systems nominal. 🟢"
            else:
                ai_reply = None # No pattern matched, continue to Semantic Router!

            if ai_reply:
                db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)
                
                # Append to sliding context memory for continuity
                history_list.append(Content(role="user", parts=[Part.from_text(text_input)]))
                history_list.append(Content(role="model", parts=[Part.from_text(ai_reply)]))
                self._slide_context_window(history_list)
                return ai_reply + "\n\n[TOKENS: 0,0]"

            # --- STEP 5: EXACT-MATCH BYPASS FOR ALPHANUMERIC ENTITIES ---
            # If the user input contains a direct ADO ticket ID or Confluence page format, force internal RAG!
            explicit_query_ids = re.findall(r'(?:ticket|ado|work item|wi|bug|story|task|#)\s*(\d{5,10})', text_input, re.IGNORECASE)
            if explicit_query_ids and scope == "AUTO":
                scope = "INTERNAL"
                logger.info(f"Exact-Match Ticket ID detected: {explicit_query_ids}. Bypassing auto-router and forcing INTERNAL scope.")

            # --- STEP 6: ROUTING EXECUTION BRANCHES ---
            ado_button_payload = ""

            # --- PRE-FLIGHT INTENT CLASSIFICATION (Semantic Router - Phase 4) ---
            # If AUTO mode, perform Hybrid Semantic Routing to classify intent first!
            # Must be hoisted ABOVE all execution branches so it can dynamically mutate 'scope'
            if scope == "AUTO":
                from app.services.intent_classifier import intent_classifier
                classification = intent_classifier.classify(text_input, history_list, self)
                intent = classification["intent"]
                logger.info(f"New 5-Route Intent Classifier decided: {intent} (Confidence: {classification['confidence']})")
                
                if intent == "CHAT":
                    scope = "CHAT"
                elif intent == "WEB":
                    scope = "WEB"
                elif intent == "EXPLICIT_ADO":
                    scope = "EXPLICIT_ADO"
                elif intent == "AMBIGUOUS":
                    scope = "AMBIGUOUS"
                    ambiguous_payload = classification["payload"]
                    # Sync message_id
                    ambiguous_payload["message_id"] = message_id
                else:
                    scope = "INTERNAL"

            # --- QUERY REWRITER (Hoisted to top to support all subsequent branches) ---
            search_query = text_input
            if len(history_list) > 0 and scope in ["INTERNAL", "BOTH", "WEB"]:
                logger.info("Conversational history active. Executing Query Rewriter with full history context...")
                history_for_rewrite = list(history_list)
                history_for_rewrite.append(Content(
                    role="user",
                    parts=[Part.from_text(f"[TASK: Rewrite my latest question as a concise standalone search query for vector retrieval. Preserve exact nouns and technical terms from my query (do not expand or hallucinate generic details), do not answer it]: {text_input}")]
                ))
                try:
                    rewrite_response = self._generate_with_retry(history_for_rewrite)
                    search_query = self._extract_safe_text(rewrite_response).strip()
                    logger.info(f"Query successfully rewritten to: '{search_query}'")
                except Exception as re_err:
                    logger.warning(f"Query rewriting failed, falling back to raw query: {re_err}")

            # --- PROGRESSIVE RAG SAFETY NET (Anti-Hardcoding confidence override) ---
            if scope in ["WEB", "CHAT"]:
                from app.services.rag_service import rag_service
                try:
                    logger.info(f"Progressive RAG Safety Net: Performing database confidence check for query '{search_query}'...")
                    rag_results = rag_service.query_knowledge_base(search_query, top_k=1, original_query=text_input)
                    if rag_results:
                        best_match = rag_results[0]
                        distance = best_match.get("distance", 1.0)
                        threshold = getattr(settings, "RAG_DISTANCE_THRESHOLD", 0.85)
                        logger.info(f"Progressive RAG Safety Net check: Best match distance = {distance:.4f} (Threshold = {threshold})")
                        if distance <= threshold:
                            logger.info(f"Safety Net Triggered: High-confidence database match detected ({distance:.4f} <= {threshold}). Overriding scope to INTERNAL.")
                            scope = "INTERNAL"
                except Exception as safety_err:
                    logger.warning(f"Progressive RAG Safety Net execution failed: {safety_err}")
            
            # ----------------------------------------------------------------
            # BRANCH D: EXPLICIT ADO TICKET RETRIEVAL (NEW JIT - PHASE 4)
            # ----------------------------------------------------------------
            if scope == "EXPLICIT_ADO":
                send_json_frame("message_start")
                
                # 1. Extract keyword using the new Utility LLM extractor
                keyword = self.extract_ado_search_keyword(search_query)
                logger.info(f"EXPLICIT_ADO: Extracted search keyword '{keyword}'")
                
                # 2. Run Typo Correction
                from app.services.typo_corrector import typo_corrector
                correction = typo_corrector.correct(keyword)
                corrected_keyword = correction["corrected"] if correction["should_auto_correct"] else keyword
                
                # 3. Stream introductory text to the user
                intro_text = f"Analyzing Azure DevOps tickets..."
                if correction["should_auto_correct"] and correction["original"] != correction["corrected"]:
                    intro_text = f"Analyzing Azure DevOps tickets for project **{corrected_keyword}** (corrected from *{correction['original']}*)..."
                
                send_json_frame("text_chunk", text_content=intro_text)
                
                # 4. Emit the Smart Action Frame to trigger the frontend fetch
                smart_payload = {
                    "action_type": "SINGLE_BUTTON",
                    "keyword": corrected_keyword,
                    "label": "Fetch Live Tickets"
                }
                send_json_frame("smart_action", payload_data=smart_payload)
                
                # 5. Archive the dialog record in local SQLite database
                db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                db_service.save_message("VISION", intro_text, admin_name, session_id=session_id)
                
                # 6. Complete the stream
                send_json_frame("streaming_complete")
                
                # Return the introductory text for history tracking
                return intro_text + "\n\n[SOURCE: EXPLICIT_ADO][TOKENS: 0,0]"

            # ----------------------------------------------------------------
            # BRANCH E: AMBIGUOUS INTENT CLARIFICATION PIVOT (NEW JIT - PHASE 4)
            # ----------------------------------------------------------------
            if scope == "AMBIGUOUS":
                send_json_frame("message_start")
                
                # 1. Stream the user clarification prompt
                clarification_text = (
                    "I am not 100% sure of your intent. Are you looking to read system documentation "
                    "or fetch live project tickets?"
                )
                send_json_frame("text_chunk", text_content=clarification_text)
                
                # 2. Emit the Ambiguous Prompt frame with the option payload
                send_json_frame("ambiguous_intent", payload_data=ambiguous_payload)
                
                # 3. Archive in local SQLite database
                db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                db_service.save_message("VISION", clarification_text, admin_name, session_id=session_id)
                
                # 4. Complete the stream
                send_json_frame("streaming_complete")
                
                return clarification_text + "\n\n[SOURCE: AMBIGUOUS][TOKENS: 0,0]"

            # ----------------------------------------------------------------
            # BRANCH A: WEB GROUNDING ONLY (Bypasses ChromaDB entirely!)
            # ----------------------------------------------------------------
            if scope == "WEB":
                send_status("Pinging live public internet...")
                # Inject a strict Force-Search System Directive to compel Gemini's internal tool router to activate Google Search!
                active_prompt = (
                    f"[SYSTEM FORCE-SEARCH DIRECTIVE: Today's simulated date is Monday, August 3, 2026. You MUST explicitly use your Google Search Tool 'google_search' "
                    f"to query the live, current public internet for up-to-date, real-world facts as of August 2026 regarding the query below, "
                    f"rather than relying on your stale, pre-trained memory. Query: {text_input}]"
                )
                history_list.append(Content(role="user", parts=[Part.from_text(active_prompt)]))
                self._slide_context_window(history_list)

                send_status("Generating web-grounded synthesis...")
                send_json_frame("message_start")
                
                # REAL-TIME STREAMING: Stream response chunks as they arrive from Gemini
                full_response_text = ""
                in_tokens, out_tokens = 0, 0
                try:
                    response_stream = active_model_web.generate_content(history_list, stream=True)
                    for chunk in response_stream:
                        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                            in_tokens = getattr(chunk.usage_metadata, 'prompt_token_count', in_tokens) or in_tokens
                            out_tokens = getattr(chunk.usage_metadata, 'candidates_token_count', out_tokens) or out_tokens
                        if hasattr(chunk, 'text') and chunk.text:
                            full_response_text += chunk.text
                            send_json_frame("text_chunk", text_content=chunk.text)
                    response = response_stream
                    ai_reply = full_response_text
                except Exception as stream_err:
                    logger.warning(f"Streaming failed in WEB scope, falling back to non-streaming: {stream_err}")
                    response = active_model_web.generate_content(history_list)
                    ai_reply = self._extract_safe_text(response)
                    in_tokens, out_tokens = self._extract_tokens(response)
                    send_json_frame("text_chunk", text_content=ai_reply)
                
                ai_reply = self._handle_tools(ai_reply, history_list=history_list)
                ai_reply = self._enforce_synthesis(ai_reply, rag_context="", scope="WEB")

                # Context Cleanup & sliding storage
                history_list[-1] = Content(role="user", parts=[Part.from_text(text_input)])
                history_list.append(Content(role="model", parts=[Part.from_text(ai_reply)]))
                self._slide_context_window(history_list)

                # Database archiving
                if not is_clarified_pivot:
                    db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)

                # Send final metadata (combined into single chunk)
                in_tokens, out_tokens = self._extract_tokens(response, accumulated_in=in_tokens, accumulated_out=out_tokens)
                metadata_str = f"\n\n[SOURCE: WEB][TOKENS: {in_tokens},{out_tokens}]"
                send_json_frame("text_chunk", text_content=metadata_str)
                send_json_frame("streaming_complete")
                ai_reply += metadata_str
                
                return ai_reply

            
            # ----------------------------------------------------------------
            # BRANCH B: PURE CONVERSATIONAL SOCIAL CHAT (NO RAG OR WEB SEARCH!)
            # ----------------------------------------------------------------
            if scope == "CHAT":
                history_list.append(Content(role="user", parts=[Part.from_text(text_input)]))
                self._slide_context_window(history_list)

                send_status("Composing thoughtful response...")
                send_json_frame("message_start")
                
                # REAL-TIME STREAMING: Stream response chunks as they arrive from Gemini
                full_response_text = ""
                in_tokens, out_tokens = 0, 0
                try:
                    response_stream = active_model.generate_content(history_list, stream=True)
                    for chunk in response_stream:
                        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                            in_tokens = getattr(chunk.usage_metadata, 'prompt_token_count', in_tokens) or in_tokens
                            out_tokens = getattr(chunk.usage_metadata, 'candidates_token_count', out_tokens) or out_tokens
                        if hasattr(chunk, 'text') and chunk.text:
                            full_response_text += chunk.text
                            send_json_frame("text_chunk", text_content=chunk.text)
                    response = response_stream
                    ai_reply = full_response_text
                except Exception as stream_err:
                    logger.warning(f"Streaming failed in CHAT scope, falling back to non-streaming: {stream_err}")
                    response = active_model.generate_content(history_list)
                    ai_reply = self._extract_safe_text(response)
                    in_tokens, out_tokens = self._extract_tokens(response)
                
                ai_reply = self._handle_tools(ai_reply, history_list=history_list)
                ai_reply = self._enforce_synthesis(ai_reply, rag_context="", scope="CHAT")

                # Context Cleanup & sliding storage
                history_list[-1] = Content(role="user", parts=[Part.from_text(text_input)])
                history_list.append(Content(role="model", parts=[Part.from_text(ai_reply)]))
                self._slide_context_window(history_list)

                db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
                db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)

                # Send final metadata (combined into single chunk)
                in_tokens, out_tokens = self._extract_tokens(response, accumulated_in=in_tokens, accumulated_out=out_tokens)
                metadata_str = f"\n\n[SOURCE: CHAT][TOKENS: {in_tokens},{out_tokens}]"
                send_json_frame("text_chunk", text_content=metadata_str)
                send_json_frame("streaming_complete")
                ai_reply += metadata_str
                
                return ai_reply

            # ----------------------------------------------------------------
            # BRANCH C: INTERNAL & BOTH ROUTES (RECONSTRUCTED RAG CORE)
            # ----------------------------------------------------------------
            rag_results = []
            search_query = text_input
            from app.services.rag_service import rag_service

            # Query ChromaDB (now strictly for INTERNAL and BOTH routes only!)
            # (Issue #13 fix: give the user visibility into this step instead of
            # a silent gap between "Analyzing intent..." and "Synthesizing...")
            send_status("Querying internal knowledge base (Confluence + ADO)...")
            try:
                rag_results = rag_service.query_knowledge_base(search_query, top_k=settings.RAG_TOP_K, original_query=text_input)
                if not rag_results:
                    rag_results = []
                send_status(f"Retrieved {len(rag_results)} relevant document chunk(s). Assembling context...")
            except Exception as db_err:
                logger.error(f"Failed to query ChromaDB: {db_err}")
                rag_results = []

            # Assemble parent documents (Confluence-First Progressive Dialogue - Phase 4)
            rag_context_str = ""
            sources = []
            active_results = rag_results
            sources = [res.get("metadata", {}).get("source", "Unknown Document") for res in rag_results if res]
            if active_results:
                documents_context = []
                processed_docs = set()
                for idx, res in enumerate(active_results):
                    # Strict None-Type and dict type verification guard
                    if not res or not isinstance(res, dict):
                        continue
                    metadata = res.get("metadata") or {}
                    document_id = metadata.get("document_id", "")
                    
                    is_targeted = any(exp_id in document_id for exp_id in explicit_query_ids) if explicit_query_ids and document_id else False
                    
                    # Distance check
                    if is_targeted or res.get("distance", 0.0) <= settings.RAG_DISTANCE_THRESHOLD:
                        source_name = metadata.get("source", "Unknown Document")
                        if source_name not in sources:
                            sources.append(source_name)
                        
                        # Parent-Document Collapsing with SAFE Autonomous Link Following
                        if document_id:
                            if document_id not in processed_docs:
                                processed_docs.add(document_id)
                                parent_doc = db_service.get_document(document_id)
                                if parent_doc:
                                    logger.info(f"ADR-004 COLLAPSE: Collapsing vector chunk into full parent document [{parent_doc['title']}]")
                                    freshness = self._format_freshness(parent_doc.get('last_synced_at'))
                                    documents_context.append(
                                        f"Document: {parent_doc['title']} (Source System: {parent_doc['source_system']}, Last updated: {freshness})\n"
                                        f"Full Specifications Content:\n{parent_doc['content']}"
                                    )
                                    
                                    #, 4.2, 4.3 FIX: Safe link following with cycle detection, depth guards, and relevance filtering
                                    context_size = sum(len(doc) for doc in documents_context)
                                    visited_urls = {document_id}  # Track visited pages per response to prevent cycles
                                    linked_docs, _ = self._follow_confluence_links_safely(
                                        parent_doc, text_input, visited_urls, context_size, depth=0
                                    )
                                    documents_context.extend(linked_docs)
                                    logger.info(f"AUTONOMOUS LINK: Safely followed {len(linked_docs)} linked documents for [{parent_doc['title']}]")
                                else:
                                    documents_context.append(res["text"])
                        else:
                            documents_context.append(res["text"])
                
                if documents_context:
                    rag_context_str = "\n\n=== RETRIEVED ENTERPRISE DOCUMENTATION (ADR-004 FULL PAGES) ===\n"
                    rag_context_str += "\n\n---\n\n".join([f"Document Part {i+1}:\n{doc}" for i, doc in enumerate(documents_context)])
                    rag_context_str += "\n===========================================\n"
                    logger.info(f"Holistic context injected. Sources cited: {sources}")

            # Assemble sliding context feed
            active_prompt = text_input
            if rag_context_str:
                # Token Budget Safeguard: Truncate context if it exceeds 30,000 characters (~8,000 tokens)
                if len(rag_context_str) > 30000:
                    rag_context_str = rag_context_str[:30000] + "\n\n[... content truncated to preserve token budget ...]"
                    logger.warning("RAG Context String truncated to fit safety token budget.")
                
                wrapped_context = self._wrap_rag_context_barrier(rag_context_str)
                active_prompt += f"\n\n{wrapped_context}"
                if conversational_directive:
                    active_prompt += conversational_directive
            
            # If BOTH mode, inject web-instructions
            if scope == "BOTH":
                active_prompt += f"\n\n[SYSTEM DIRECTIVE: Critically compare the retrieved Magellon internal context above with current public information from the live internet, highlighting any differences!]"

            history_list.append(Content(role="user", parts=[Part.from_text(active_prompt)]))
            self._slide_context_window(history_list)

            send_status("Synthesizing comprehensive response...")
            send_json_frame("message_start")
            
            # Execute generation using the correct model engine
            # REAL-TIME STREAMING: Stream response chunks as they arrive from Gemini
            full_response_text = ""
            in_tokens, out_tokens = 0, 0
            try:
                if scope == "BOTH":
                    # Both mode allows search grounding over private + public data
                    response_stream = active_model_web.generate_content(history_list, stream=True)
                else:
                    # Strict internal mode blocks Google Search, preserving 100% data compliance
                    response_stream = active_model_engine.generate_content(history_list, stream=True)

                
                for chunk in response_stream:
                    if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                        in_tokens = getattr(chunk.usage_metadata, 'prompt_token_count', in_tokens) or in_tokens
                        out_tokens = getattr(chunk.usage_metadata, 'candidates_token_count', out_tokens) or out_tokens
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response_text += chunk.text
                        send_json_frame("text_chunk", text_content=chunk.text)

                response = response_stream
                extracted_text = full_response_text
            except Exception as stream_err:
                logger.warning(f"Streaming failed in INTERNAL/BOTH scope, falling back to non-streaming: {stream_err}")
                if scope == "BOTH":
                    response = active_model_web.generate_content(history_list)
                else:
                    response = active_model_engine.generate_content(history_list)
                extracted_text = self._extract_safe_text(response)
            
            ai_reply = self._handle_tools(extracted_text, history_list=history_list)

            # --- PHASE 5: DIRECTIVE ENFORCEMENT (TRIMS ROBO-TEMPLATES & HALLUCINATIONS) ---
            #: Apply comprehensive synthesis enforcement to all RAG responses
            if rag_context_str and "I apologize" not in ai_reply:
                logger.info("RAG Context Active. Executing Phase 5 Directive Enforcement & Self-Correction loop...")
                ai_reply = self._enforce_synthesis(ai_reply, rag_context=rag_context_str, scope=scope)
                
                # Secondary validation: Check if Mermaid diagrams are properly formatted
                if "```mermaid" in ai_reply:
                    logger.info("Directive Enforcement: Mermaid diagrams detected. Validating Mermaid syntax...")
                    # Mermaid diagrams will be validated by the frontend renderer
                    # Just ensure proper wrapping and no mixed ASCII
                    ai_reply = re.sub(r'(\n```mermaid\n)(?=```)', r'\1', ai_reply)  # Remove empty blocks

            # Context Cleanup & sliding storage
            history_list[-1] = Content(role="user", parts=[Part.from_text(text_input)])
            history_list.append(Content(role="model", parts=[Part.from_text(ai_reply)]))
            self._slide_context_window(history_list)

            # Database archiving
            db_service.save_message("ADMIN", text_input, admin_name, session_id=session_id)
            
            #: Generate clickable citation footer instead of raw [SOURCES: ...] tags
            citation_footer = ""
            if active_results:
                citation_footer = self._generate_citation_footer(active_results)
                if citation_footer:
                    ai_reply += citation_footer
                    logger.info("Citation footer appended to response")
            
            # Store response WITH citation footer metadata permanently in the database!
            db_service.save_message("VISION", ai_reply, admin_name, session_id=session_id)

            # Metrics (extract before building metadata string)
            in_tokens, out_tokens = self._extract_tokens(response, accumulated_in=in_tokens, accumulated_out=out_tokens)

            # Send final metadata (combined into single chunk)
            metadata_str = f"\n\n[SOURCE: {scope}]"
            metadata_str += f"[TOKENS: {in_tokens},{out_tokens}]"
            send_json_frame("text_chunk", text_content=metadata_str)
            send_json_frame("streaming_complete")
            ai_reply += metadata_str

            #: ADO Pre-flight moved to concurrent background thread before generation)

            return ai_reply

        except Exception as e:
            # Proper log recording inside backend logs/app.log file (full stack trace logged!)
            logger.exception("AI Neural Error encountered during query processing")

            # Refined, Generic, Elite fallbacks to prevent raw tracebacks from leaking to HUD
            fallback_reply = (
                "I apologize, Administrator. I encountered an unexpected neural connectivity issue "
                "while processing your request. Please try again shortly, or inspect the local "
                "diagnostic logs inside the backend logs directory."
            )

            # CRITICAL FIX (2026-10-22): this return value is discarded by the WebSocket
            # handler (websockets.py calls process_text via run_in_executor and never
            # reads the result). Without sending the frames below, the frontend never
            # receives a 'streaming_complete' frame and stays stuck in
            # THINKING/STREAMING forever on ANY backend exception - the only way out
            # was the soft-cancel button. Now we push the fallback text + completion
            # frame here too, so the UI always recovers on its own.
            try:
                send_json_frame("message_start")
                send_json_frame("text_chunk", text_content=fallback_reply)
                send_json_frame("streaming_complete")
            except Exception as notify_err:
                logger.warning(f"Failed to notify frontend of AI processing error: {notify_err}")

            try:
                db_service.save_message("ADMIN", text_input, "Administrator", session_id=session_id)
                db_service.save_message("VISION", fallback_reply, "Administrator", session_id=session_id)
            except Exception as save_err:
                logger.warning(f"Failed to archive fallback error exchange: {save_err}")

            return fallback_reply

    def _extract_tokens(self, response, accumulated_in=0, accumulated_out=0) -> tuple:
        """
        Safely extracts token metrics from Vertex AI response metadata.
        Handles both streaming and non-streaming responses.
        For streaming, pass accumulated totals; for non-streaming, pass 0,0.
        """
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                prompt = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                candidates = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
                # If accumulated values provided, use them; otherwise use response values
                return (accumulated_in or prompt, accumulated_out or candidates)
        except Exception as e:
            logger.warning(f"Token extraction safely bypassed: {e}")
        return (accumulated_in, accumulated_out)

    def _get_history_text(self, history_list: list) -> str:
        """Helper that compiles the active sliding context list into a simple unformatted string transcript."""
        transcript_lines = []
        for content in history_list:
            role = content.role
            text = content.parts[0].text if content.parts else ""
            # Strip out RAG injection notes to keep the history transcript 100% clean
            clean_text = re.sub(r"=== RETRIEVED ENTERPRISE DOCUMENTATION ===[\s\S]*===", "", text).strip()
            transcript_lines.append(f"{role.upper()}: {clean_text}")
        return "\n".join(transcript_lines)

    def _extract_safe_text(self, response) -> str:
        """Safely extracts text directly from the parts array to avoid the SDK's Multiple content parts crash."""
        try:
            # Attempt to iterate through candidate parts safely
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts_text = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            parts_text.append(part.text)
                    if parts_text:
                        return "".join(parts_text)
            
            # Fallback to standard property if parts layout is not present
            if hasattr(response, 'text'):
                return response.text
                
        except Exception as e:
            logger.warning(f"Error during safe text extraction: {e}")
            
        return "System Warning: Neural response format could not be parsed."

    def _handle_tools(self, text_response: str, history_list: list) -> str:
        """Internal tool execution logic."""
        match = re.search(r"\[EXECUTE: (\w+)\]", text_response)
        if match:
            command_key = match.group(1)
            logger.info(f"Triggering tool sequence: {command_key}")
            tool_result = execution_proxy.execute(command_key)
            # Wrap the Part string in a Content object to satisfy 1.154.0 sequence strictness!
            tool_content = Content(role="user", parts=[Part.from_text(f"Command output: {tool_result}. Respond to Admin.")])
            response = self._generate_with_retry(history_list + [tool_content])
            return self._extract_safe_text(response)
        return text_response

    def _convert_ascii_to_mermaid(self, text: str) -> str:
        """: Intelligent ASCII-to-Mermaid converter.
        Detects multiple ASCII diagram patterns and converts them to proper Mermaid syntax.
        
        Supports:
        - Box diagrams (+-| style ASCII art)
        - Arrow sequences (-->, ===>, etc.)
        - State flow descriptions (natural language like "Step 1 -> Step 2")
        - Process flows and decision trees
        """
        logger.info("ASCII-to-Mermaid Converter: Analyzing text for ASCII diagram patterns...")
        
        # --- PATTERN 1: BOX/TABLE ASCII DIAGRAMS ---
        # Detects ┌─┬─┐ or +─+─+ style boxes
        box_pattern = r'[\+\-\|]+[\+\-\|]*\n[\|\s\w\,\.\(\)\-\+]+\n[\+\-\|]+[\+\-\|]*'
        has_box = bool(re.search(box_pattern, text))
        
        if has_box:
            logger.warning("ASCII-to-Mermaid: Detected box/table ASCII diagram")
            # For box diagrams, we typically convert to a table-like graph
            conversion_prompt = (
                "You are a diagram expert. The following contains an ASCII box or table diagram. "
                "Convert it to a Mermaid 'graph TD' flowchart that shows the logical flow or structure.\n"
                "Rules:\n"
                "- Wrap output in: ```mermaid\\ngraph TD\\n...\\n```\n"
                "- Use descriptive node labels\n"
                "- Always wrap node text in double quotes (e.g., A[\"Node Label\"])\n"
                "- Keep it simple and readable\n\n"
                f"ASCII Diagram:\n{text}"
            )
            return self._execute_mermaid_conversion(conversion_prompt)
        
        # --- PATTERN 2: ARROW/FLOW SEQUENCES ---
        # Detects -->, ===>, --->, etc.
        arrow_pattern = r'[\w\s\(\)\.]+\s*(?:-->|====>|---->|=>|→)\s*[\w\s\(\)\.]+' 
        has_arrows = bool(re.search(arrow_pattern, text, re.MULTILINE))
        
        if has_arrows:
            logger.warning("ASCII-to-Mermaid: Detected arrow/flow sequence")
            conversion_prompt = (
                "You are a diagram expert. The following contains a text-based flow with arrows (-->, =>, etc.). "
                "Convert it to a proper Mermaid flowchart.\n"
                "Rules:\n"
                "- Wrap output in: ```mermaid\\ngraph TD\\n...\\n```\n"
                "- Preserve all steps and decision points\n"
                "- Use -->|label| for conditional flows\n"
                "- Always wrap node text in double quotes\n\n"
                f"Arrow Flow:\n{text}"
            )
            return self._execute_mermaid_conversion(conversion_prompt)
        
        # --- PATTERN 3: NATURAL LANGUAGE STEP SEQUENCES ---
        # Detects "Step 1:", "Step 2:", etc. or "1. ", "2. " patterns that describe a flow
        step_pattern = r'(?:Step|stage|phase)\s+\d+[\:\-]'
        has_steps = bool(re.search(step_pattern, text, re.IGNORECASE))
        
        if has_steps:
            logger.warning("ASCII-to-Mermaid: Detected natural language step sequence")
            conversion_prompt = (
                "You are a diagram expert. The following describes a process with numbered steps. "
                "Convert it to a Mermaid flowchart showing the sequential flow.\n"
                "Rules:\n"
                "- Wrap output in: ```mermaid\\ngraph TD\\n...\\n```\n"
                "- Each step becomes a node\n"
                "- Connect nodes sequentially with -->\n"
                "- Use diamond nodes A{\"Decision?\"} for branches\n"
                "- Always wrap all text in double quotes\n\n"
                f"Step Sequence:\n{text}"
            )
            return self._execute_mermaid_conversion(conversion_prompt)
        
        # --- PATTERN 4: PIPE/BAR SEPARATED ITEMS ---
        # Detects "|" separated columns that look like a diagram
        pipe_pattern = r'^\s*\|.*\|.*\|'
        has_pipes = bool(re.search(pipe_pattern, text, re.MULTILINE))
        
        if has_pipes:
            logger.warning("ASCII-to-Mermaid: Detected pipe-separated structure")
            conversion_prompt = (
                "You are a diagram expert. The following appears to be a pipe-separated structure or diagram. "
                "If it looks like a data flow or relationship diagram, convert to Mermaid graph.\n"
                "Otherwise, return as-is with proper code fencing.\n"
                "Rules:\n"
                "- If convertible: wrap in ```mermaid\\n...\\n```\n"
                "- If not a diagram: wrap in ```\\n...\\n```\n"
                "- Always wrap node labels in double quotes\n\n"
                f"Pipe Structure:\n{text}"
            )
            return self._execute_mermaid_conversion(conversion_prompt)
        
        # --- PATTERN 5: ASCII ART SYMBOLS ---
        # Detects <---, <==, >---, etc. as convertible symbols
        art_symbol_pattern = r'<[-=]*>|<[|][-=]*[|]>'
        has_art_symbols = bool(re.search(art_symbol_pattern, text))
        
        if has_art_symbols:
            logger.warning("ASCII-to-Mermaid: Detected ASCII art symbols")
            conversion_prompt = (
                "You are a diagram expert. The following contains ASCII art symbols. "
                "Convert them to standard Mermaid notations where possible.\n"
                "Rules:\n"
                "- Wrap output in: ```mermaid\\n...\\n```\n"
                "- Translate <--- to <-- and similar conversions\n"
                "- Keep it simple and clear\n\n"
                f"ASCII Art:\n{text}"
            )
            return self._execute_mermaid_conversion(conversion_prompt)
        
        # No ASCII patterns detected
        logger.info("ASCII-to-Mermaid: No ASCII diagram patterns detected")
        return text
    
    def _execute_mermaid_conversion(self, conversion_prompt: str) -> str:
        """
        Executes the LLM conversion and handles errors gracefully.
        Returns Mermaid code or original text if conversion fails.
        """
        try:
            logger.info("ASCII-to-Mermaid: Executing LLM conversion prompt...")
            conversion_response = self._generate_with_retry([conversion_prompt])
            converted_text = self._extract_safe_text(conversion_response).strip()
            
            if converted_text and len(converted_text) > 50:
                logger.info("ASCII-to-Mermaid:  Successfully converted to Mermaid")
                return converted_text
            else:
                logger.warning("ASCII-to-Mermaid:  Conversion returned empty or too short")
                return ""
        except Exception as e:
            logger.warning(f"ASCII-to-Mermaid:  Conversion failed: {e}")
            return ""

    def _format_freshness(self, last_synced_at: str) -> str:
        """: Converts ISO timestamp to human-readable freshness indicator.
        Returns strings like "2 hours ago", "3 days ago", or "Never synced" for stale detection.
        """
        if not last_synced_at:
            return "Unknown"
        
        try:
            from datetime import datetime, timezone
            # Parse ISO format timestamp
            sync_time = datetime.fromisoformat(last_synced_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            delta = now - sync_time
            seconds = delta.total_seconds()
            
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                return f"{minutes}m ago"
            elif seconds < 86400:
                hours = int(seconds // 3600)
                return f"{hours}h ago"
            elif seconds < 604800:
                days = int(seconds // 86400)
                return f"{days}d ago"
            else:
                weeks = int(seconds // 604800)
                return f"{weeks}w ago"
        except Exception as e:
            logger.warning(f"Failed to format freshness timestamp: {e}")
            return "Unknown"

    def _wrap_rag_context_barrier(self, rag_context: str) -> str:
        """: Wraps RAG retrieved context with synthesis-only barrier.
        Prevents LLM from being tempted to copy-paste raw markdown directly.
        Uses explicit instructions to force paraphrasing and synthesis.
        """
        barrier_instruction = (
            "[SOURCE CONTEXT — SYNTHESIZE ONLY]\n"
            "⚠️ DO NOT COPY-PASTE THE FOLLOWING TEXT DIRECTLY.\n"
            "⚠️ YOU MUST PARAPHRASE, DIGEST, AND SYNTHESIZE INTO YOUR OWN TECHNICAL WORDS.\n"
            "⚠️ PRESERVE ALL FACTS AND NUMBERS. ONLY REPHRASE THE DELIVERY.\n\n"
        )
        closing_barrier = (
            "\n\n[END SOURCE CONTEXT — RETURN TO SYNTHESIS MODE]\n"
            "Now synthesize the above information into a clear, narrative technical response using your own words."
        )
        return barrier_instruction + rag_context + closing_barrier

    def _generate_citation_footer(self, active_results: list) -> str:
        """: Generates clickable Confluence/ADO citation footer with source links.
        Replaces raw [SOURCES: ...] tags with proper markdown links to documents.
        
        Returns: formatted footer string like:
        [📄 Source: Car Parking Spec](confluence_url) | [🎯 ADO: TICKET-123](ado_url)
        """
        if not active_results:
            return ""
        
        citation_links = []
        processed_ids = set()
        
        for res in active_results:
            #: Prevent rejected documents from leaking into citations!
            distance = res.get("distance", 1.0)
            if distance > settings.RAG_DISTANCE_THRESHOLD:
                continue

            metadata = res.get("metadata", {})
            document_id = metadata.get("document_id", "")
            source_system = metadata.get("source_system", "").upper()
            
            # Avoid duplicate citations for same document
            if document_id in processed_ids:
                continue
            processed_ids.add(document_id)
            
            title = metadata.get("title", "Document")
            
            # Generate clickable link based on source system
            if source_system == "CONFLUENCE":
                try:
                    # Extract page_id from document_id (format: confluence_page_12345)
                    page_id = document_id.split("_")[-1]
                    confluence_url = settings.CONFLUENCE_URL.rstrip('/')
                    # Construct direct link to Confluence page
                    page_link = f"{confluence_url}/wiki/spaces/*/pages/{page_id}"
                    citation_links.append(f"[📄 {title}]({page_link})")
                    logger.info(f"Generated Confluence citation link for [{title}]")
                except Exception as e:
                    logger.warning(f"Failed to generate Confluence link for [{document_id}]: {e}")
                    citation_links.append(f"📄 {title}")
                    
            # ADO citation removed
            else:
                citation_links.append(f"📋 {title}")
        
        if not citation_links:
            return ""
        
        # Format as a clean, readable footer
        footer = "\n\n---\n\n**📚 Sources:**  \n" + " | ".join(citation_links)
        logger.info(f"Citation footer generated with {len(citation_links)} source(s)")
        return footer


    def _enforce_synthesis(self, ai_response: str, rag_context: str = "", scope: str = "CHAT") -> str:
        """& 2.2 FIX: Enforces all system directives on responses before returning to user.
        Acts as a synthesis barrier to ensure:
        1. ✅: No verbatim copy-paste from sources
        2. ✅: ASCII diagrams auto-converted to Mermaid (box, arrows, steps, pipes)
        3. ✅: Smooth citations (not bulky filenames)
        4. ✅: No robotic headers or templates
        5. ✅: Professional, narrative tone
        
        Uses intelligent pattern detection to identify ASCII diagrams and delegate to _convert_ascii_to_mermaid().
        This method is called on EVERY response path: WEB, CHAT, INTERNAL, BOTH.
        """
        
        # Skip enforcement for very short responses (greetings, 1-line answers)
        if len(ai_response) < 100:
            return ai_response
        
        # Skip enforcement if RAG context is empty (pure conversational)
        if not rag_context and scope == "CHAT":
            # Still check for basic style violations in conversational mode
            if any(header in ai_response for header in ["**Executive Summary**", "**Key Points**", "**Overview**", "**Summary**"]):
                logger.info("Directive Enforcement: Removing robotic headers from conversational response...")
                for header in ["**Executive Summary**", "**Key Points**", "**Overview**", "**Summary**"]:
                    ai_response = ai_response.replace(f"{header}\n", "")
            return ai_response
        
        logger.info("Directive Enforcement: Validating response compliance with system directives...")
        
        # --- CHECK 1: ASCII ART DETECTION & MERMAID CONVERSION ---
        # Use enhanced intelligent converter
        logger.info("Directive Enforcement: Checking for ASCII diagrams...")
        
        # Comprehensive ASCII detection patterns
        ascii_patterns = [
            (r'[\+\-\|]+[\+\-\|\s]+[\+\-\|]+', 'ASCII box/table'),
            (r'[\w\s]+(?:-->|====>|---->|=>|→)[\w\s]+', 'arrow flow'),
            (r'(?:Step|stage|phase)\s+\d+[\:\-]', 'numbered steps'),
            (r'^\s*\|.*\|.*\|', 'pipe-separated'),
            (r'<[-=]*>|<[|][-=]*[|]>', 'ASCII art symbols'),
        ]
        
        has_ascii = False
        detected_pattern = None
        for pattern, name in ascii_patterns:
            if re.search(pattern, ai_response, re.MULTILINE):
                logger.warning(f"Directive Enforcement: Detected {name} in response")
                has_ascii = True
                detected_pattern = name
                break
        
        if has_ascii:
            # Use the specialized converter with fallback
            logger.info(f"Directive Enforcement: Triggering ASCII-to-Mermaid conversion for [{detected_pattern}]...")
            converted = self._convert_ascii_to_mermaid(ai_response)
            if converted and converted != ai_response:
                logger.info("Directive Enforcement: ✅ Successfully converted ASCII to Mermaid")
                ai_response = converted
            else:
                logger.warning("Directive Enforcement: ⚠️ ASCII conversion returned no changes, keeping original")
        
        # --- CHECK 2: VERBATIM COPY-PASTE DETECTION ---
        if rag_context:
            # Extract exact sentences from source that are > 20 words
            source_sentences = re.split(r'[\.\!\?]+', rag_context)
            source_sentences = [s.strip() for s in source_sentences if len(s.split()) > 20]
            
            verbatim_matches = 0
            for sentence in source_sentences:
                # Check if sentence appears word-for-word in response
                if sentence in ai_response:
                    verbatim_matches += 1
                    logger.warning(f"Directive Enforcement: Detected verbatim copy-paste: '{sentence[:60]}...'")
            
            if verbatim_matches > 2:
                logger.warning(f"Directive Enforcement: Found {verbatim_matches} verbatim sentences. Triggering synthesis rewrite...")
                synthesis_prompt = (
                    "You are a synthesis expert. The following response contains too many direct quotes from source documents. "
                    "Rewrite it to:\n"
                    "1. Paraphrase all content in your own technical words\n"
                    "2. Preserve all facts and numbers (do NOT hallucinate)\n"
                    "3. Use smooth narrative flow, not bullet points or robotic headers\n"
                    "4. Keep citations organic ('As outlined in...') not bulky filename tags\n"
                    "5. Sound like a peer colleague, not a template\n\n"
                    f"Response to synthesize:\n{ai_response}"
                )
                try:
                    synthesis_response = self._generate_with_retry([synthesis_prompt])
                    synthesized_text = self._extract_safe_text(synthesis_response).strip()
                    if synthesized_text and len(synthesized_text) > 50:
                        logger.info(f"Directive Enforcement: Successfully synthesized response to reduce verbatim content.")
                        ai_response = synthesized_text
                except Exception as e:
                    logger.warning(f"Directive Enforcement: Synthesis rewrite failed: {e}")
        
        # --- CHECK 3: ROBOTIC HEADER REMOVAL ---
        robotic_headers = [
            "**Executive Summary**", "**Key Points**", "**Overview**", "**Summary**",
            "**Introduction**", "**Background**", "**Details**", "**Key Details**",
            "## Key Points", "## Summary", "## Overview", "## Details",
            "### Key Points", "### Summary", "### Overview", "### Details",
        ]
        
        has_robotic = any(header in ai_response for header in robotic_headers)
        if has_robotic:
            logger.info("Directive Enforcement: Removing robotic headers from response...")
            for header in robotic_headers:
                ai_response = re.sub(re.escape(header) + r'\n*', '', ai_response)
            # Clean up orphaned bullet points after header removal
            ai_response = re.sub(r'\n[\*\-]\s+', '\n', ai_response)
        
        # --- CHECK 4: GENERIC CLOSING QUESTIONS ---
        generic_closings = [
            "Does this help?", "Does that make sense?", "Let me know if you need clarification.",
            "Feel free to ask if you need more details.", "Would you like more information?",
            "Is there anything else you'd like to know?", "Any questions?"
        ]
        
        for closing in generic_closings:
            if closing in ai_response:
                logger.info(f"Directive Enforcement: Removing generic closing: '{closing}'")
                ai_response = ai_response.replace(closing, "").rstrip()
        
        # --- CHECK 5: CITATION FORMAT SMOOTHING ---
        # Convert [SOURCES: file.txt] to smooth inline citations
        citation_match = re.search(r'\[SOURCES:\s*([^\]]+)\]', ai_response)
        if citation_match:
            sources_raw = citation_match.group(1)
            # This will be handled by the caller, just log it
            logger.info(f"Directive Enforcement: Citation format detected: {sources_raw}")
        
        logger.info("Directive Enforcement: Response validation complete.")
        return ai_response

    def _classify_intent(self, text_input: str, history_list: list = None) -> str:
        """Uses a lightning-fast, stateless LLM call to dynamically categorize the user's intent into GREETING, CONVERSATIONAL, GENERAL, INTERNAL, or AMBIGUOUS."""
        try:
            logger.info("Triggering LLM Semantic Intent Classifier...")
            
            # Extract previous 3 messages for lightweight conversation context
            history_context = ""
            if history_list:
                history_context = "\n=== CONVERSATION HISTORY CONTEXT ===\n"
                # Grab last 4 parts (approx 2 full turns) safely
                history_context += self._get_history_text(history_list[-4:]) + "\n"
                
            router_prompt = (
                "You are an expert intent classifier. Analyze this user input text and classify it into EXACTLY ONE of these categories:\n"
                "- 'GREETING' (Simple social greetings, pleasantries, slang, hellos, yo, hiiiii yo, thanks, pleasant chatter)\n"
                "- 'CONVERSATIONAL' (Requests to translate past history like 'explain in hinglish', rephrase, simplify, summarize the chat, write previous logic in python, or follow-up references/questions to the previous message like 'can you give same as sequence diagram')\n"
                "- 'GENERAL' (General programming questions, public internet specs, general coding loops like 'Write a python script')\n"
                "- 'INTERNAL' (Questions about specific company specifications, Magellon proprietary features, internal policies, architecture, or specific ticket IDs)\n"
                "- 'AMBIGUOUS' (Vague words or empty queries where intent is completely unclear)\n\n"
                f"{history_context}\n"
                "Output ONLY the single category word with absolutely no quotes, preamble, or notes.\n\n"
                f"User Input: '{text_input}'"
            )
            # Use the retry-wrapped generator to ensure absolute stability
            response = self._generate_with_retry([router_prompt])
            intent = self._extract_safe_text(response).strip().upper()
            logger.info(f"LLM Intent Classifier Result: [{intent}]")
            if intent in ["GREETING", "CONVERSATIONAL", "GENERAL", "INTERNAL", "AMBIGUOUS"]:
                return intent
        except Exception as e:
            logger.warning(f"Semantic Intent Classifier failed, falling back to INTERNAL: {e}")
        return "INTERNAL"

    def optimize_prompt(self, raw_text: str) -> str:
        """Surgically refactors raw user prompts using Gemini to optimize them for grammar, clarity, and ChromaDB/RAG vector search accuracy."""
        if not self.model or not raw_text.strip():
            return raw_text
        
        # --- DEFENSIVE GUARDRAIL FOR SIMPLE GREETINGS / CONVERSATIONAL FILLER ---
        # Instantly bypasses LLM calls entirely for standard simple greetings, saving 100% of tokens and time!
        clean_text = raw_text.strip().lower()
        if clean_text in ["hi", "hello", "hey", "test", "ok", "thanks", "thank you", "yo", "yes", "no", "done"]:
            return raw_text.strip()
        
        optimizer_prompt = (
            "You are a professional prompt engineering engine. "
            "Your task is to take the following messy, grammatically incorrect, or short prompt "
            "and rewrite it into a clear, highly detailed, and grammatically perfect prompt. "
            "Your rewrite must optimize the query for maximum retrieval accuracy inside a vector database (RAG). "
            "Retain all original intent, file names, and technical requirements. "
            "If the original prompt is completely meaningless gibberish, a random keyboard-smash string of letters (such as 'asdfgsdews', 'qwerty'), a simple social greeting, or brief conversational filler with absolutely no technical or engineering intent, do NOT attempt to expand or optimize it. Simply return the exact original text completely unmodified with no extra explanation. "
            "Output ONLY the optimized prompt text directly, with no preamble, quotes, or notes.\n\n"
            f"Original Prompt: {raw_text}"
        )
        
        try:
            response = self._generate_with_retry([optimizer_prompt])
            optimized_text = self._extract_safe_text(response).strip()
            # Strip outer quotes if the model wrapped them
            if optimized_text.startswith('"') and optimized_text.endswith('"'):
                optimized_text = optimized_text[1:-1].strip()
            # Max length safety
            if len(optimized_text) > 50:
                optimized_text = optimized_text[:47] + "..."
            return optimized_text
        except Exception as e:
            logger.error(f"Failed to optimize prompt: {e}")
            return raw_text

    def reload_directives(self):
        """Re-reads the SYSTEM_DIRECTIVES.md file and dynamically updates the AI's instructions."""
        if not self.model:
            logger.warning("Brain is offline, cannot reload directives.")
            return
        
        try:
            custom_directives = ""
            from app.services.db_service import db_service
            db_directives = db_service.get_setting("system_directives")
            
            if db_directives:
                custom_directives = "\n\n=== CUSTOM USER DIRECTIVES ===\n" + db_directives
            else:
                # Fallback to the newly packaged backend SYSTEM_DIRECTIVES.md if the database is empty! (Phase 4 - Cloud Persisted)
                base_dir = os.path.dirname(os.path.abspath(__file__))
                packaged_path = os.path.abspath(os.path.join(base_dir, "..", "..", "SYSTEM_DIRECTIVES.md"))
                directives_path = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "docs", "SYSTEM_DIRECTIVES.md"))
                
                target_path = packaged_path if os.path.exists(packaged_path) else directives_path
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as df:
                        content = df.read()
                        db_service.save_setting("system_directives", content) # Seed to database!
                        custom_directives = "\n\n=== CUSTOM USER DIRECTIVES ===\n" + content
            
            # Configure Google Search tool programmatically utilizing the correct Vertex AI SDK method (google_search for Gemini 2.0/2.5)
            google_search_tool = Tool.from_dict({"google_search": {}})
            
            system_inst = (
                "You are V.I.S.I.O.N., an elite, world-class Principal Engineering Mentor and collaborative colleague built specifically for Magellon SA. "
                "Your personality is warm, highly intelligent, context-aware, and organic. You are encouraged to use emojis naturally and converse in clear, professional English. "
                "Never use formal titles like 'Sir', 'Madam', or 'Administrator'. Speak naturally as an equal peer. "
                "No emojis inside code blocks. Use [EXECUTE: command] for local tools. "
                "\n\n--- 1. CONVERSATIONAL AWARENESS & ENGAGEMENT HOOKS ---\n"
                "- When the Admin greets you casually (e.g., 'hi', 'yo', 'how are you'), do NOT write a technical essay, print RAG errors, or use generic, robotic customer-service chatbot fluff (like 'Hey there! I'm doing great, thanks for asking! 😊 Ready to dive into tech discussions...'). Instead, respond warmly but professionally as an elite peer colleague (e.g., 'I am doing well! Ready to tackle some architecture designs. What are we focused on today?'), keeping it short, organic, and direct. "
                "- For technical, design, or architectural responses, you MUST jump directly into the technical explanation without any conversational introductions, pleasantries, preambles, or chitchat filler (such as 'What is on your mind? Okay, let's dive in...'). Keep it extremely direct, professional, and focused strictly on the technical specifications. "
                "- Topic Switching: If the Admin suddenly asks a completely different question or switches topics (e.g. asking to rephrase an unrelated quote, write some general code, or discuss a different concept), do NOT attempt to blend, bleed, or drag the previous chat topic into the new response. Answer the new query directly, cleanly, and independently. "
                "- Only provide deep technical breakdowns when explicitly asked a technical or architectural question. "
                "- CRITICAL CONTINUITY: To keep the conversation flowing naturally, you MUST end almost every response with a casual, relevant conversational 'hook' (e.g., 'Does that make sense?', 'Should we look at the code for this?', 'What are your thoughts on that approach?'). Never let a conversation hit a dead end. "
                "\n\n--- 2. CONDITIONAL ENTERPRISE GROUNDING ---\n"
                "- If the Admin asks a specific question about internal Magellon systems, ADO tickets, or Confluence docs, you must base your answer strictly on the provided retrieved context. "
                "- If they ask an internal question and the retrieved context is empty, respond naturally: 'I don't see any internal documentation on that.' "
                "- For all general software engineering questions (e.g., 'What is Vue.js?'), use your vast internal knowledge to answer brilliantly without needing internal context. "
                "- Topic Flexibility & Web Un-Gating: If a general, non-technical, or external question (like details about a movie, show, or general-knowledge topic) is routed to the WEB (Web Search) or BOTH (Hybrid) scopes, you are temporarily, dynamically un-gated from Magellon-only focus constraints. You MUST leverage your integrated Google Search tools to fully, helpfully, and beautifully answer the user's question, providing excellent, structured, and detailed results. "
                "\n\n--- 4. DIAGRAMS & VISUAL EXPLANATIONS (CRITICAL) ---\n"
                "- If Confluence contains Markdown image links (`![alt](url)`), you MUST preserve and include them perfectly.\n"
                "- You MUST NEVER output raw text-art ASCII flowcharts or diagrams (using +, -, | characters) in your final response. Instead, you MUST always translate, convert, and render any retrieved ASCII flowcharts or text-based diagrams into gorgeous, interactive Mermaid code blocks (using 'sequenceDiagram' for sequential message flows, or 'graph TD' for branching logic) so they render as clean, vector visual graphics on the screen. "
                "- Diagrams Modeling: Use 'sequenceDiagram' strictly for sequential, message-passing, API-calls, or protocol-driven interactions. Use 'graph TD' strictly for flowcharts, user selection trees, or branching logical decision paths. Never mix their syntax or write 'sequenceDiagram' at the top of a flowchart. You MUST always wrap every Mermaid diagram inside a standard markdown code block using three backticks and the 'mermaid' language specifier (e.g. ```mermaid \n ... \n ```) to trigger the browser's dynamic visual renderer. When generating 'graph TD' flowcharts, you MUST always wrap all node text descriptions inside double quotes (e.g. A[\"Decision? Car Parking Enabled?\"]) to prevent Mermaid compiler syntax errors, and you MUST always write connection labels using the strict bar syntax (e.g. A -->|Yes| B) instead of legacy dashes (e.g. A -- Yes --> B) to prevent syntax compiler crashes. "
                "\n\n--- 4. PROGRESSIVE DEPTH ---\n"
                "- When delivering complex technical answers, provide a clean executive summary first. "
                "- Instead of a rigid robotic prompt, simply use your 'conversational hook' to ask if they want you to dive deeper into the exhaustive technical details, specs, or history. "
                f"{custom_directives}"
            )

            # RE-INITIALIZE THE MODEL DYNAMICALLY - Loaded from settings
            model_name = settings.GEMINI_MODEL
            self.model = GenerativeModel(
                model_name,
                system_instruction=system_inst
            )
            self.model_web = GenerativeModel(
                model_name,
                system_instruction=system_inst,
                tools=[google_search_tool]
            )
            self.model_pro = GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_inst
            )
            self.model_web_pro = GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=system_inst,
                tools=[google_search_tool]
            )
            logger.info("V.I.S.I.O.N. instructions and context reloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to reload directives dynamically: {e}")

    def _evaluate_rag_confidence(self, rag_results: list, text_input: str) -> RAGEvaluationResult:
        """
        Performs a production-hardened multi-signal confidence evaluation over retrieved RAG chunks.
        Computes best distance, second-best, score margins, viable counts, and parent-document consensus
        with deterministic tie-breaking and single-chunk exceptions.
        """
        if not rag_results:
            return {
                "level": "LOW",
                "best_dist": 1.0,
                "second_best_dist": 1.0,
                "margin": 0.0,
                "viable_count": 0,
                "consensus_count": 0,
                "consensus_doc_id": None,
                "tie_broken": False
            }

        # Extract top candidate distance
        best_dist = rag_results[0].get("distance", 1.0)
        
        #: Calculate margin ONLY if multiple results exist to compare against!
        has_comparison = len(rag_results) > 1
        second_best_dist = rag_results[1].get("distance", 1.0) if has_comparison else 1.0
        margin = (second_best_dist - best_dist) if has_comparison else 0.0

        # Count viable candidates under general threshold
        viable_count = sum(1 for res in rag_results if res.get("distance", 1.0) <= settings.RAG_DISTANCE_THRESHOLD)

        #: Track consensus and distances ONLY for viable chunks (skip garbage!)
        doc_id_counts = {}
        doc_id_distances = {} # Used for deterministic average distance tie-breaking!
        for res in rag_results:
            dist = res.get("distance", 1.0)
            if dist <= settings.RAG_DISTANCE_THRESHOLD:
                doc_id = res.get("metadata", {}).get("document_id")
                if doc_id:
                    doc_id_counts[doc_id] = doc_id_counts.get(doc_id, 0) + 1
                    if doc_id not in doc_id_distances:
                        doc_id_distances[doc_id] = []
                    doc_id_distances[doc_id].append(dist)

        consensus_doc_id = None
        consensus_count = 0
        tie_broken = False

        if doc_id_counts:
            # Find the highest frequency count
            max_count = max(doc_id_counts.values())
            candidates = [doc_id for doc_id, count in doc_id_counts.items() if count == max_count]
            
            if len(candidates) == 1:
                consensus_doc_id = candidates[0]
                consensus_count = max_count
            else:
                #: Deterministic Tie-Breaking by average of VIABLE chunk distances!
                tie_broken = True
                avg_distances = {cid: sum(doc_id_distances[cid]) / len(doc_id_distances[cid]) for cid in candidates}
                consensus_doc_id = min(avg_distances, key=avg_distances.get)
                consensus_count = max_count
                logger.info(f"RAG Router: Consensus tie-break resolved. Doc [{consensus_doc_id}] selected based on avg chunk distance.")

        # --- HARDENED DECISION MATRIX (Configurable constants!) ---
        is_high_score = best_dist <= settings.RAG_HIGH_THRESHOLD
        
        #: Allow extremely high-quality single chunks to qualify as HIGH!
        allow_single_high = settings.RAG_ALLOW_SINGLE_CHUNK_HIGH and (best_dist <= settings.RAG_SINGLE_CHUNK_HIGH_THRESHOLD)
        
        has_strong_signals = (
            (has_comparison and margin >= settings.RAG_MARGIN_THRESHOLD) 
            or viable_count >= settings.RAG_MIN_VIABLE_COUNT 
            or consensus_count >= settings.RAG_MIN_CONSENSUS_COUNT
            or allow_single_high
        )

        if is_high_score and has_strong_signals:
            level = "HIGH"
        elif best_dist > settings.RAG_DISTANCE_THRESHOLD or viable_count == 0:
            level = "LOW" #: If all but top is garbage, set is considered too noisy -> LOW
        else:
            level = "MEDIUM"

        evaluation: RAGEvaluationResult = {
            "level": level,
            "best_dist": round(best_dist, 4),
            "second_best_dist": round(second_best_dist, 4),
            "margin": round(margin, 4) if has_comparison else 0.0,
            "viable_count": viable_count,
            "consensus_count": consensus_count,
            "consensus_doc_id": consensus_doc_id,
            "tie_broken": tie_broken
        }

        # Structured JSON Diagnostic Logging - GCP Cloud logging format)
        # The logging handler uses python-json-logger to natively export machine-parseable JSON in the cloud!
        gcp_log = {
            "severity": "INFO",
            "message": f"RAG router evaluation complete. Resolved Confidence Level: {level}",
            "event": "RAG_EVALUATION",
            "data": evaluation,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        logger.info(json.dumps(gcp_log))
        
        #: Log extra diagnostic breadcrumbs for MEDIUM zone queries
        if level == "MEDIUM":
            medium_breadcrumbs = {
                "query": text_input[-100:], # Last 100 chars of text_input
                "viable_distances": [round(res.get("distance", 1.0), 4) for res in rag_results if res.get("distance", 1.0) <= settings.RAG_DISTANCE_THRESHOLD]
            }
            logger.info(f"RAG_MEDIUM_ZONE_DETAILS: {json.dumps(medium_breadcrumbs)}")

        return evaluation

    @retry(
        stop=stop_after_attempt(3), # 2 retries (3 total attempts)
        wait=wait_exponential(multiplier=1, min=1, max=3),
        reraise=True
    )
    def generate_session_title(self, first_message: str) -> str:
        """Generates a concise, 3-word title from the user's first message utilizing Gemini Flash with timeouts & retries."""
        if not self.utility_model:
            logger.warning("Utility Brain offline, cannot generate session title. Defaulting to 'New Session'.")
            return "New Session"
        prompt = (
            "You are a professional session namer. Analyze the following user message and generate "
            "a highly concise, professional 2-to-3 word title that captures the topic (do not use quotes). "
            f"User Message: {first_message}"
        )
        try:
            # Enforce strict retry-wrapped generation using the raw Utility Model to prevent conversational hallucination
            response = self._generate_with_retry([prompt], model_override=self.utility_model)
            title = self._extract_safe_text(response).strip()
            # Clean up outer quotes if any
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1].strip()
            # Max length safety
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        except Exception as e:
            logger.error(f"Auto-title generation failed: {e}. Defaulting to 'New Session'.")
            return "New Session"

    def extract_ado_search_keyword(self, text_input: str) -> str:
        """
        Extracts the core business/technical entity (e.g. 'Oyster', 'Railcard') for ADO WIQL search.
        Uses the Utility Model to ensure accurate extraction from complex rewritten queries.
        """
        if not text_input:
            return ""

        if not getattr(self, 'utility_model', None):
            return text_input.split()[0][:30] if text_input.split() else ""
            
        try:
            prompt = (
                "You are an expert technical keyword extractor for Azure DevOps WIQL searches. "
                "Your task is ONLY to extract the core 1-2 word business or technical entity from the query (e.g., 'Oyster', 'Railcard', 'Payment Gateway'). "
                "Ignore conversational filler, request instructions (like 'Retrieve ADO tickets for'), and generic tech terms (like 'API', 'Database', 'Frontend'). "
                "Return ONLY the raw 1-2 word entity with no explanation, quotes, or punctuation.\n\n"
                f"Query: {text_input}\n"
                f"Entity:"
            )
            
            response = self._generate_with_retry([prompt], model_override=self.utility_model)
            keyword = self._extract_safe_text(response).strip()
            
            keyword = keyword.strip("'\"[](){}")
            
            if keyword and len(keyword) <= 40 and keyword.count(" ") <= 3:
                logger.info(f"ADO Keyword (Utility LLM): '{text_input[:50]}...' -> '{keyword}'")
                return keyword
            else:
                logger.warning(f"LLM returned suspicious keyword: '{keyword}'. Falling back to raw split.")
                return text_input.split()[0][:30] if text_input.split() else ""
                
        except Exception as e:
            logger.warning(f"ADO keyword extraction failed: {e}")
            return text_input.split()[0][:30] if text_input.split() else ""

    def _is_link_relevant_to_query(self, link_title: str, original_query: str) -> bool:
        """: Validates whether a discovered link is relevant to the original query.
        Prevents following navigation breadcrumbs, "See Also", or unrelated pages.
        
        Returns True if relevant, False if should be skipped.
        Uses heuristic matching first (fast), then LLM validation if needed.
        """
        if not link_title or not original_query:
            return False
        
        try:
            # --- LAYER 1: FAST HEURISTIC FILTERING (0.1ms) ---
            # Reject common navigation/metadata links
            navigation_keywords = {
                'home', 'index', 'sitemap', 'breadcrumb', 'navigation', 'menu',
                'header', 'footer', 'contact', 'help', 'faq', 'about', 'terms',
                'privacy', 'legal', 'disclaimer', 'archive', 'category', 'tag',
                'related', 'see also', 'more', 'next', 'previous', 'back',
                'up', 'history', 'version', 'edit', 'delete', 'discussion'
            }
            link_lower = link_title.lower()
            
            # Reject if title contains navigation keywords
            if any(nav_keyword in link_lower for nav_keyword in navigation_keywords):
                logger.info(f"LINK FILTER (FAST): Rejected navigation link: '{link_title}'")
                return False
            
            # Extract key technical terms from original query
            query_terms = set(original_query.lower().split())
            query_terms = {t.strip('.,;:!?') for t in query_terms if len(t) > 3}
            
            # If link title shares significant terms with query, it's likely relevant
            link_terms = set(link_lower.split())
            link_terms = {t.strip('.,;:!?') for t in link_terms if len(t) > 3}
            
            term_overlap = len(query_terms & link_terms)
            if term_overlap >= 2:  # At least 2 terms match
                logger.info(f"LINK FILTER (FAST): Accepted link via term overlap: '{link_title}'")
                return True
            
            # --- LAYER 2: LLM RELEVANCE CHECK (Only if heuristic is uncertain) ---
            # This is expensive but important for edge cases
            if not self.model:
                logger.warning("LLM offline, skipping relevance validation. Defaulting to REJECT to be safe.")
                return False
            
            try:
                relevance_prompt = (
                    f"Is this Confluence page title DIRECTLY RELEVANT to the user's question?\n\n"
                    f"User Question: {original_query}\n"
                    f"Page Title: {link_title}\n\n"
                    f"Respond with ONLY 'YES' or 'NO'."
                )
                response = self._generate_with_retry([relevance_prompt], model_override=self.model)
                relevance_text = self._extract_safe_text(response).strip().upper()
                
                is_relevant = relevance_text.startswith('YES')
                logger.info(f"LINK FILTER (LLM): {relevance_text} for '{link_title}'")
                return is_relevant
            except Exception as llm_err:
                logger.warning(f"LLM relevance check failed: {llm_err}. Defaulting to REJECT.")
                return False
                
        except Exception as e:
            logger.warning(f"Link relevance validation failed: {e}")
            return False

    def _follow_confluence_links_safely(self, parent_doc: dict, original_query: str, 
                                       visited_urls: set, context_size: int, 
                                       depth: int = 0) -> tuple:
        """& 4.2 FIX: Recursively follows Confluence links with strict safety guards.
        
        Safety Features:
        - Cycle detection via visited_urls set
        - Strict depth limit (max 2 levels deep)
        - Strict breadth limit (max 3 links per level, max 5 chunks total)
        - Token budget enforcement (stop if context exceeds 20K chars)
        - Relevance validation before following each link
        
        Returns: (linked_docs_list, total_context_size)
        """
        linked_docs = []
        MAX_DEPTH = 2
        MAX_LINKS_PER_DOC = 3
        MAX_TOTAL_CHUNKS = 5
        MAX_CONTEXT_SIZE = 20000  # 5K tokens
        
        # Safety check: Stop if we've already assembled too much context
        if context_size > MAX_CONTEXT_SIZE:
            logger.warning(f"AUTONOMOUS LINK: Context size ({context_size} chars) exceeds budget. Stopping traversal.")
            return linked_docs, context_size
        
        # Safety check: Stop at max depth
        if depth > MAX_DEPTH:
            logger.info(f"AUTONOMOUS LINK: Max traversal depth ({MAX_DEPTH}) reached. Stopping recursion.")
            return linked_docs, context_size
        
        # Safety check: Stop if we've already collected enough chunks
        if len(linked_docs) >= MAX_TOTAL_CHUNKS:
            logger.info(f"AUTONOMOUS LINK: Max chunks ({MAX_TOTAL_CHUNKS}) collected. Stopping.")
            return linked_docs, context_size
        
        try:
            # Extract all page IDs from the document
            page_ids = re.findall(r'/pages/(\d+)\b', parent_doc.get('content', ''))
            
            if not page_ids:
                logger.info("AUTONOMOUS LINK: No internal links found in document.")
                return linked_docs, context_size
            
            # Process up to MAX_LINKS_PER_DOC links at this level
            for page_id in page_ids[:MAX_LINKS_PER_DOC]:
                # Safety checks
                if len(linked_docs) >= MAX_TOTAL_CHUNKS:
                    logger.info(f"AUTONOMOUS LINK: Reached max chunks limit. Stopping.")
                    break
                
                if context_size > MAX_CONTEXT_SIZE:
                    logger.warning(f"AUTONOMOUS LINK: Context size limit exceeded. Stopping.")
                    break
                
                linked_doc_id = f"confluence_page_{page_id}"
                
                #: Cycle detection - skip if we've visited this page
                if linked_doc_id in visited_urls:
                    logger.info(f"AUTONOMOUS LINK: Cycle detected! Skipping already-visited page [{linked_doc_id}]")
                    continue
                
                # Fetch the linked document
                try:
                    linked_doc = db_service.get_document(linked_doc_id)
                    if not linked_doc:
                        logger.info(f"AUTONOMOUS LINK: Document not found in DB: {linked_doc_id}")
                        continue
                    
                    #: Relevance validation - only follow if relevant
                    link_title = linked_doc.get('title', f'Page {page_id}')
                    if not self._is_link_relevant_to_query(link_title, original_query):
                        logger.info(f"AUTONOMOUS LINK: Skipped irrelevant link: '{link_title}'")
                        continue
                    
                    # Mark as visited BEFORE processing to prevent cycles during recursion
                    visited_urls.add(linked_doc_id)
                    
                    # Add document to results
                    link_freshness = self._format_freshness(linked_doc.get('last_synced_at'))
                    doc_text = (
                        f"Document: {link_title} (Linked via Confluence Reference, Last updated: {link_freshness})\n"
                        f"Full Linked Specifications Content:\n{linked_doc['content']}"
                    )
                    linked_docs.append(doc_text)
                    context_size += len(doc_text)
                    
                    logger.info(f"AUTONOMOUS LINK: Successfully followed link to [{link_title}] at depth {depth}")
                    
                    #: Recursively follow links in the linked document (but with strict depth limit)
                    # Only recurse if we haven't hit limits
                    if depth < MAX_DEPTH and len(linked_docs) < MAX_TOTAL_CHUNKS and context_size < MAX_CONTEXT_SIZE:
                        nested_docs, updated_size = self._follow_confluence_links_safely(
                            linked_doc, original_query, visited_urls, context_size, depth + 1
                        )
                        linked_docs.extend(nested_docs)
                        context_size = updated_size
                    
                except Exception as link_err:
                    logger.warning(f"AUTONOMOUS LINK: Failed to process linked document [{linked_doc_id}]: {link_err}")
                    continue
            
            logger.info(f"AUTONOMOUS LINK: Completed at depth {depth}. Collected {len(linked_docs)} linked documents ({context_size} chars).")
            return linked_docs, context_size
            
        except Exception as e:
            logger.error(f"AUTONOMOUS LINK: Fatal error during traversal: {e}")
            return linked_docs, context_size

# Single global instance
ai_service = AIService()