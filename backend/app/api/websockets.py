# ============================================================================
# PROJECT V.I.S.I.O.N. - STATEFUL WEBSOCKET & STATE DAEMON GATEWAY
# ============================================================================
# File Description:
# This module acts as the primary real-time communication portal.
# It manages bi-directional WebSocket connections, handles binary voice uploads,
# triggers AI processing streams, and runs the background hardware telemetry daemon.
# Upon connection, it automatically re-hydrates the client UI with their local
# SQLite dialogue history scoped strictly to the selected session.
# ============================================================================

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from starlette.websockets import WebSocketState # Import standard socket state identifiers
from app.core.config import settings
from app.services.ai_service import ai_service # Core AI processing logic
from app.services.db_service import db_service # Local SQLite database utility
from vertexai.generative_models import Content, Part
import logging
import os
import uuid
import json
import asyncio

# Setup module logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Define directory to cache incoming raw voice recordings
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True) # Ensure cache directory exists

async def _run_background_title_update(session_id: str, first_msg: str, admin_name: str, websocket: WebSocket):
    """Generates and updates a session title asynchronously in the background, streaming the result to client."""
    try:
        # Generate and update in separate thread pool to prevent blocking ASGI
        loop = asyncio.get_event_loop()
        new_title = await loop.run_in_executor(None, ai_service.generate_session_title, first_msg)
        
        if new_title and new_title != "New Session":
            success = db_service.update_session_title_idempotent(session_id, new_title, admin_name)
            if success:
                # Stream the real-time rename update back to the browser!
                try:
                    from starlette.websockets import WebSocketState
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(f"[SYSTEM_SESSION_RENAME: {session_id}:{new_title}]")
                        logger.info(f"Broadcasted session rename packet for [{session_id}] -> [{new_title}].")
                except RuntimeError as re_err:
                    logger.warning(f"Could not stream session rename packet (socket already closed): {re_err}")
                except Exception as stream_err:
                    logger.warning(f"Could not stream session rename packet (client disconnected): {stream_err}")
    except Exception as e:
        logger.error(f"Background title generation failed: {e}")

@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    Stateful WebSocket listener that establishes the pipeline, streams historical 
    conversations scoped to session_id, and processes text/audio requests concurrently.
    """
    # Accept the incoming connection request from the browser
    await websocket.accept()
    logger.info(f"WebSocket connection established with client: {websocket.client.host}")

    # Extract session_id dynamically from handshake query parameters
    session_id = websocket.query_params.get("session_id", "default_session")
    admin_name = websocket.query_params.get("admin_name")
    
    if not admin_name:
        logger.error(f"WebSocket Connection Rejected: admin_name query parameter is missing from the handshake.")
        await websocket.close(code=1008) # Policy Violation
        return
        
    logger.info(f"Session binding request received: session_id=[{session_id}] for user=[{admin_name}]")

    # --- PER-CONNECTION CONCURRENCY-SAFE MEMORY QUEUE (PHASE 4) ---
    # Instantiated locally in this connection context to prevent multi-admin memory leaks!
    connection_history = []
    
    # Pre-populate connection history with the last 10 messages for sliding context window
    logger.info("Pre-populating Vertex AI sliding context history from SQL logs...")
    past_context = db_service.get_chat_history_for_session(session_id, admin_name, limit=settings.MAX_CONTEXT_TURNS)
    for msg in reversed(past_context):
        sender = str(msg.get("sender", "")).upper().strip()
        text = msg.get("text")
        if sender == "ADMIN":
            connection_history.append(Content(role="user", parts=[Part.from_text(text)]))
        elif sender == "VISION":
            connection_history.append(Content(role="model", parts=[Part.from_text(text)]))

    logger.info(f"Vertex AI context reconstructed. Turns in memory: {len(connection_history)}")

    try:
        while True:
            # Wait asynchronously for the next network message frame from the HUD
            message = await websocket.receive()
            vision_response = None
            text_query_used = ""

            if "bytes" in message:
                # --- NATIVE MULTIMODAL AUDIO PROCESSING ---
                # Intercept raw binary audio stream from mic recording
                audio_data = message["bytes"]
                logger.info(f"Received raw WebM audio buffer ({len(audio_data)} bytes)")

                # Cache raw bytes into a unique temp WebM file on disk
                temp_file_name = f"{uuid.uuid4()}.webm"
                temp_file_path = os.path.join(TEMP_AUDIO_DIR, temp_file_name)
                with open(temp_file_path, "wb") as f:
                    f.write(audio_data)

                # Process temp audio through Gemini multimodal engine scoped to local memory
                vision_response = ai_service.transcribe_audio(temp_file_path, history_list=connection_history, session_id=session_id)
                text_query_used = "[Voice Command transmitted]"

                # Instantly purge temp file from disk after processing to prevent storage bloat
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

                # Stream the transcribed response as JSON frames (# & #2)
                if vision_response:
                    message_id = f"msg_{uuid.uuid4().hex[:8]}"
                    from app.services.websocket_framing_service import websocket_framer
                    try:
                        if websocket.client_state == WebSocketState.CONNECTED:
                            # 1. Message Start Frame
                            await websocket.send_text(websocket_framer.build_message_start(message_id))
                            # 2. Text Chunk Frame (The whole response)
                            await websocket.send_text(websocket_framer.build_text_chunk(message_id, vision_response))
                            # 3. Complete Frame
                            await websocket.send_text(websocket_framer.build_streaming_complete(message_id))
                    except Exception as ws_err:
                        logger.warning(f"Failed to transmit voice response frames: {ws_err}")

            elif "text" in message:
                # --- MANUAL TEXT PROMPT OVERRIDE ---
                # Intercept plain text query submitted from HUD console
                text_data = message["text"]
                logger.info(f"Received manual override text query: '{text_data}'")
                text_query_used = text_data

                # Generate unique ID per query (# )
                message_id = f"msg_{uuid.uuid4().hex[:8]}"

                # Process text through sliding window context manager scoped to local memory
                # Call the core AI processing block in a background thread executor!
                # This unblocks the FastAPI event loop, allowing JIT status updates to stream instantly
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    ai_service.process_text,
                    text_data,
                    connection_history,
                    session_id,
                    websocket,
                    loop,
                    message_id
                )

                # --- IDEMPOTENT AUTO-TITLE BACKGROUND UPDATE TRIGGER ---                # Trigger title expansion asynchronously if current session is named "New Session", "General Session", or "Default Session"
                try:
                    active_sessions = db_service.get_chat_sessions(admin_name)
                    matching_session = next((s for s in active_sessions if s["session_id"] == session_id), None)
                    if matching_session and matching_session["title"] in ["New Session", "General Session", "Default Session"] and text_query_used:
                        logger.info("First message detected! Spawning background auto-title routine...")
                        # Run as native concurrent background async task
                        asyncio.create_task(_run_background_title_update(session_id, text_query_used, admin_name, websocket))
                except Exception as t_err:
                    logger.warning(f"Failed to check/trigger background auto-title update: {t_err}")

            else:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text("I'm sorry, Administrator, I was unable to process that request.")
                except Exception as ws_send_err:
                    logger.warning(f"Failed to stream error response over WebSocket (client disconnected): {ws_send_err}")

    except WebSocketDisconnect:
        logger.warning(f"WebSocket connection closed by client: {websocket.client.host}")
    except Exception as e:
        logger.error(f"An error occurred inside WebSocket communication channel: {e}")
    finally:
        # Clear local array to garbage collect memory
        connection_history.clear()
        logger.info(f"WebSocket closed gracefully. Local context memory cleared for session [{session_id}].")
