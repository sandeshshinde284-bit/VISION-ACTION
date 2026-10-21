
# --- Step 1: Import necessary tools from the FastAPI framework ---
# We need APIRouter to organize our code in a modular way.
# We need WebSocket and WebSocketDisconnect to handle the connection itself.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# --- Step 2: Import Python's built-in logging library ---
# This is a professional way to print messages to the terminal. It's better than print()
# because it can add timestamps, log levels (INFO, ERROR), and can be configured to write to files.
import logging

# Configure the logger to show messages of level INFO and higher.
logger = logging.getLogger(__name__)

# --- Step 3: Create a "Router" ---
# Analogy: Think of a large book. A router is like the table of contents for a specific chapter.
# It groups all related endpoints (in this case, our WebSocket endpoints) together.
# This keeps our main file (main.py) clean and organized.
router = APIRouter()

# --- Step 4: Define the WebSocket Endpoint ---
# The '@router.websocket("/ws/audio")' is a "decorator". It's a special piece of Python syntax
# that attaches functionality to the function defined immediately below it.
# It tells FastAPI: "Any client that tries to open a WebSocket connection to the address '/ws/audio'
# should be handled by the 'websocket_endpoint' function."
@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    This is an 'async' function. This is crucial. It means this function can 'pause'
    and 'resume' without blocking the entire server.
    
    The 'websocket: WebSocket' part is a type hint. It tells FastAPI to provide us with a
    special 'websocket' object that has methods like .accept(), .receive_text(), and .send_text().
    """
    # --- Step 5: Accept the connection ---
    # Analogy: This is like picking up the ringing telephone. The client is calling,
    # and we are now formally accepting the connection. This must be the first thing you do.
    await websocket.accept()
    logger.info(f"WebSocket connection established with client: {websocket.client.host}")
    
    try:
        # --- Step 6: Create an infinite loop to listen for messages ---
        # A WebSocket is a persistent, long-lived connection. So, we need a loop
        # that keeps running, waiting for messages, as long as the client is connected.
        while True:
            # The 'await' keyword is the heart of 'async' programming. It tells Python to
            # PAUSE the function right here and wait patiently for a message to arrive from the client.
            # While it's waiting, other parts of our FastAPI server can still handle other requests.
            data = await websocket.receive_text()
            
            logger.info(f"Received message from client: '{data}'")
            
            # --- Step 7: Echo the message back to the client ---
            # We use the same 'websocket' object to send a message back down the same open "pipe".
            # We format the string to make it clear this is a response from the server.
            await websocket.send_text(f"Echo from J.A.R.V.I.S.: {data}")
            
    except WebSocketDisconnect:
        # This 'except' block is a special, graceful way to handle the client hanging up
        # (e.g., closing the browser tab). The 'while' loop will break, and this code will run.
        logger.warning(f"WebSocket connection closed by client: {websocket.client.host}")
    except Exception as e:
        # This is a general "catch-all" for any other unexpected errors that might happen
        # during the connection, so our server doesn't crash.
        logger.error(f"An error occurred in the WebSocket connection: {e}")