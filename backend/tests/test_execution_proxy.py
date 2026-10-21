# /backend/tests/test_execution_proxy.py

from app.services.execution_proxy import execution_proxy

def test_git_status():
    """Test that git_status is whitelisted and tries to execute."""
    result = execution_proxy.execute("git_status")
    # Even if it's not a git repo, the proxy should have TRIED to run it
    # resulting in a specific git error message.
    assert "On branch" in result or "not a git repository" in result or "Not a git repository" in result

def test_unauthorized_command():
    """Test that unauthorized commands are blocked."""
    result = execution_proxy.execute("rm_rf_slash")
    assert "not authorized" in result

def test_argument_sanitization():
    """Test that arguments are properly quoted/sanitized."""
    # We try to inject a second command via arguments
    result = execution_proxy.execute("list_files", args=["-la; whoami"])
    # If sanitization works, 'dir' should try to find a file literally named '-la; whoami'
    # and fail, rather than running 'whoami'.
    assert "File Not Found" in result or "cannot find" in result or "Invalid switch" in result
    assert "w114216" not in result # Ensure the injected whoami didn't run

if __name__ == "__main__":
    print("Running Proxy Tests...")
    try:
        test_git_status()
        print("✅ Git Status Test Passed")
        test_unauthorized_command()
        print("✅ Security Block Test Passed")
        test_argument_sanitization()
        print("✅ Sanitization Test Passed")
        print("\nAll SecureExecutionProxy tests PASSED!")
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
