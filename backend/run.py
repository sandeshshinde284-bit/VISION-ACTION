# /backend/run.py

import os
import certifi
import uvicorn

if __name__ == "__main__":
    # --- THE SSL FIX ---
    # We use 'pip-system-certs' (installed via requirements.txt) which 
    # automatically patches 'certifi' to use the Windows Trust Store.
    # This allows Python to trust corporate proxies like Zscaler.
    
    # Force Google Cloud SDK to use standard HTTP/REST transport instead of gRPC.
    # This makes it use Python's requests layer which is 100% patched by pip-system-certs!
    os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"

    # Get the path to the certifi certificate bundle (now patched by pip-system-certs)
    certifi_path = certifi.where()
    
    # Set environment variables for the SSL context to use this path
    # This ensures that 'requests', 'httpx', and other libraries use the correct certs.
    os.environ["SSL_CERT_FILE"] = certifi_path
    os.environ["REQUESTS_CA_BUNDLE"] = certifi_path
    
    print("--- SSL Certificate Fix Applied ---")
    print(f"Using certificate bundle from certifi: {certifi_path}")
    print("-----------------------------------")
    
    # Now, we start uvicorn programmatically instead of from the command line.
    # This ensures it runs in the same process where we've just set the environment variables.
    uvicorn.run(
        "app.main:app",       # The same 'app.main:app' path
        host="0.0.0.0",
        port=8000,
        reload=False           # With reload enabled
    )
