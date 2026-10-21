# /backend/app/services/execution_proxy.py

import subprocess
import logging
import shlex
from typing import Dict, List, Optional

# Set up logging
logger = logging.getLogger(__name__)

class SecureExecutionProxy:
    """
    The SecureExecutionProxy is the 'Guard' of the system.
    It ensures that the AI can only execute a pre-approved set of safe commands.
    It prevents raw shell access and sanitizes all inputs.
    """

    def __init__(self):
        # Define the whitelist of allowed commands.
        # Each key is a command name, and the value is the actual base command.
        self.allowed_commands: Dict[str, str] = {
            "git_status": "git status",
            "git_branch": "git branch",
            "list_files": "cmd /c dir",    # Added 'cmd /c' for Windows built-in
            "date": "cmd /c date /T",      # Added 'cmd /c' for Windows built-in
            "whoami": "whoami"
        }
        logger.info("SecureExecutionProxy initialized with command whitelist.")

    def execute(self, command_key: str, args: Optional[List[str]] = None) -> str:
        """
        Executes a whitelisted command with optional arguments.
        """
        if command_key not in self.allowed_commands:
            logger.warning(f"SECURITY ALERT: Blocked unauthorized command attempt: '{command_key}'")
            return f"Error: Command '{command_key}' is not authorized."

        base_command = self.allowed_commands[command_key]
        
        # Build the full command string
        full_command = base_command
        if args:
            # SHLEX.QUOTE is critical. It prevents "command injection" by escaping
            # any special characters in the arguments.
            sanitized_args = " ".join([shlex.quote(str(arg)) for arg in args])
            full_command = f"{base_command} {sanitized_args}"

        logger.info(f"Executing secure command: {full_command}")

        try:
            # Run the command and capture the output
            # shell=False is a security best practice to avoid shell injection.
            result = subprocess.run(
                full_command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {e.stderr}")
            return f"Error executing command: {e.stderr}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during execution: {e}")
            return f"System error during execution: {str(e)}"

# Create a single instance to be used by the orchestrator
execution_proxy = SecureExecutionProxy()
