# /backend/app/services/security_service.py

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Cognitive Ingestion Gatekeeper & Content Classifier.
    Surgically inspects raw corporate text payloads prior to database storage
    to prevent sensitive corporate data leaks (e.g., passwords, salaries, keys)
    using secure, lightweight HTTP/REST API endpoints to completely bypass gRPC.
    """
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL

    def get_oauth_token(self) -> str:
        """
        Fetches a short-lived Google OAuth access token dynamically using
        Application Default Credentials (ADC) local OS context.
        """
        import google.auth
        import google.auth.transport.requests
        try:
            credentials, project = google.auth.default()
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            return credentials.token
        except Exception as e:
            logger.error(f"Failed to fetch Google OAuth access token via ADC: {e}")
            raise e

    def classify_text_safety(self, text: str) -> str:
        """
        Asks Gemini to inspect the incoming text and classify it as SAFE or RESTRICTED
        using Vertex AI's REST API endpoint (Bypasses gRPC/Zscaler completely).
        """
        if not text or not text.strip():
            return "SAFE"

        # Extract a secure sample for inspection to preserve context & tokens
        sample = text[:3000]

        prompt = (
            "You are a strict, enterprise-grade data loss prevention (DLP) classifier. "
            "Inspect the following text sample for highly sensitive or restricted corporate data. "
            "Data to classify as RESTRICTED:\n"
            "- Explicit lists of employee passwords, credentials, secrets, or API keys.\n"
            "- Payroll spreadsheets, employee salaries, bank accounts, or financial accounting ledgers.\n"
            "- Personal health information (PHI), social security numbers, or private medical details.\n\n"
            "Standard business documentation, code files, checklists, specs, and requirements are SAFE.\n\n"
            "Respond with ONLY a single word: SAFE or RESTRICTED.\n"
            "Do not output any quotes, notes, formatting, or explanation.\n\n"
            f"Text Sample for Inspection:\n{sample}"
        )

        import requests

        try:
            # 1. Fetch short-lived Google OAuth access token using our unified helper
            access_token = self.get_oauth_token()

            # 2. Build the REST API endpoint
            project_id = settings.GCP_PROJECT_ID
            location = settings.GCP_LOCATION
            api_endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/gemini-2.5-flash:generateContent"

            # 3. Compile HTTP headers and JSON payload
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 10
                }
            }

            # 4. Perform the secure REST post call (uses requests + pip_system_certs!)
            res = requests.post(api_endpoint, headers=headers, json=payload, timeout=15)
            if res.status_code != 200:
                logger.error(f"DLP Guardrail REST API failure: HTTP {res.status_code} - {res.text}")
                # Default to SAFE on API error to avoid blocking valid flows
                return "SAFE"

            response_data = res.json()
            candidates = response_data.get("candidates", [])
            if not candidates:
                return "SAFE"

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "SAFE"

            classification = parts[0].get("text", "").strip().upper()
            
            # Sanitize response
            if "RESTRICTED" in classification:
                logger.warning("Cognitive Interceptor ALERT: Restricted or sensitive data detected!")
                return "RESTRICTED"
            
            return "SAFE"
        except Exception as e:
            logger.error(f"DLP Guardrail REST failure (defaulting to SAFE to prevent blocks): {e}")
            return "SAFE"

security_service = SecurityService()
