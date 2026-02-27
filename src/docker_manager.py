"""Cross-platform Docker container management for Selenium"""
import os
import time
from typing import Tuple, Optional

CONTAINER_NAME = "selenium-chrome"
IMAGE_NAME = "selenium/standalone-chrome:latest"
PORT = "4444"
SELENIUM_URL = f"http://localhost:{PORT}/wd/hub"


def is_running_in_container() -> bool:
    """
    Detect whether the current process is running inside a Docker container.

    Checks for:
    - /.dockerenv file (present in all Docker containers on Linux)
    - DOCKER_CONTAINER env var (set explicitly in docker-compose.yml)
    - /proc/1/cgroup containing 'docker' or 'containerd'
    """
    if os.path.exists("/.dockerenv"):
        return True
    if os.getenv("DOCKER_CONTAINER", "").strip().lower() in ("1", "true", "yes"):
        return True
    try:
        with open("/proc/1/cgroup", "r") as f:
            return any("docker" in line or "containerd" in line for line in f)
    except Exception:
        pass
    return False


def _remote_url() -> Optional[str]:
    """Return SELENIUM_REMOTE_URL if configured, else None."""
    url = os.getenv("SELENIUM_REMOTE_URL", "").strip()
    return url if url else None


def _check_remote_selenium(remote_url: str) -> bool:
    """Return True if the remote Selenium server is healthy."""
    import requests
    try:
        status_url = remote_url.replace("/wd/hub", "/status")
        response = requests.get(status_url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def ensure_selenium_container() -> bool:
    """
    Ensure Selenium is available, adapting to the current environment.

    Decision logic:
    - Running in a Docker container  → HTTP-ping SELENIUM_REMOTE_URL only
                                       (no Docker SDK; sidecar is managed by Compose)
    - Running locally, SELENIUM_REMOTE_URL set → HTTP-ping that URL
    - Running locally, no SELENIUM_REMOTE_URL  → Docker SDK: start/reuse a local
                                                  selenium container, then export its
                                                  URL via os.environ so page_search.py
                                                  picks it up automatically

    Returns:
        bool: True if Selenium is ready, False otherwise
    """
    remote_url = _remote_url()

    # ── containerised or explicit remote URL ─────────────────────────────────
    if remote_url or is_running_in_container():
        target = remote_url or SELENIUM_URL  # fallback to localhost inside container
        print(f"[*] Checking remote Selenium at {target}...")
        if _check_remote_selenium(target):
            print("[+] Remote Selenium is ready")
            return True
        print("[!] Remote Selenium is not reachable")
        return False

    # ── local Docker SDK path ────────────────────────────────────────────────
    print("[*] Checking Selenium container (local Docker)...")
    
    try:
        import docker
        from docker.errors import DockerException, NotFound, APIError
        client = docker.from_env()

        # Test Docker connection
        try:
            client.ping()
        except Exception as e:
            print(f"[!] Docker is not running or not accessible: {e}")
            return False

        # Check if container is already running
        try:
            container = client.containers.get(CONTAINER_NAME)
            if container.status == "running":
                print("[+] Selenium container is already running")
                print(f"[*] Container URL: {SELENIUM_URL}")
                os.environ["SELENIUM_REMOTE_URL"] = SELENIUM_URL
                return True
            elif container.status == "exited":
                print("[*] Starting existing Selenium container...")
                container.start()
                _wait_for_container(container)
                print("[+] Selenium container started successfully")
                print(f"[*] Container URL: {SELENIUM_URL}")
                os.environ["SELENIUM_REMOTE_URL"] = SELENIUM_URL
                return True
            else:
                print(f"[!] Container in unexpected state: {container.status}")
                return False
                
        except NotFound:
            # Container doesn't exist, create it
            print("[*] Creating new Selenium container...")
            return _create_selenium_container(client)

    except Exception as e:
        # Import guard: docker SDK may not be available in all environments
        try:
            from docker.errors import DockerException
            if isinstance(e, DockerException):
                print(f"[!] Docker error: {e}")
                print("[!] Make sure Docker is installed and running")
                return False
        except ImportError:
            pass
        print(f"[!] Unexpected error: {e}")
        return False

def _create_selenium_container(client) -> bool:
    """
    Create and start a new Selenium container.
    
    Args:
        client: Docker client instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from docker.errors import NotFound, APIError
        # Check if image exists locally
        try:
            client.images.get(IMAGE_NAME)
            print("[*] Using existing Selenium image")
        except NotFound:
            print("[*] Pulling Selenium image (this may take a few minutes)...")
            client.images.pull(IMAGE_NAME)
            print("[+] Image pulled successfully")
        
        # Create and start container
        container = client.containers.run(
            IMAGE_NAME,
            name=CONTAINER_NAME,
            ports={'4444/tcp': PORT},
            detach=True,
            shm_size='2g',  # Increase shared memory for Chrome
            remove=False
        )
        
        print("[*] Waiting for Selenium to be ready...")
        _wait_for_container(container)
        
        print("[+] Selenium container created and started successfully")
        print(f"[*] Container URL: {SELENIUM_URL}")
        # Expose URL so page_search.py uses the container instead of a local ChromeDriver
        os.environ["SELENIUM_REMOTE_URL"] = SELENIUM_URL
        return True

    except APIError as e:
        print(f"[!] Failed to create container: {e}")
        return False
    except Exception as e:
        print(f"[!] Unexpected error creating container: {e}")
        return False

def _wait_for_container(container, max_wait: int = 30) -> bool:
    """
    Wait for container to be fully ready.
    
    Args:
        container: Docker container instance
        max_wait: Maximum seconds to wait
        
    Returns:
        bool: True if ready, False if timeout
    """
    import requests
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            container.reload()
            if container.status != "running":
                time.sleep(1)
                continue
                
            # Try to connect to Selenium
            response = requests.get(f"{SELENIUM_URL}/status", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        
        time.sleep(1)
    
    print("[!] Timeout waiting for container to be ready")
    return False

def stop_selenium_container() -> bool:
    """
    Stop the Selenium container.
    
    Returns:
        bool: True if stopped successfully, False otherwise
    """
    try:
        import docker
        from docker.errors import NotFound
        client = docker.from_env()
        container = client.containers.get(CONTAINER_NAME)

        print("[*] Stopping Selenium container...")
        container.stop(timeout=10)
        print("[+] Container stopped successfully")
        return True
        
    except NotFound:
        print("[*] Container not found (already stopped or removed)")
        return True
    except Exception as e:
        print(f"[!] Error stopping container: {e}")
        return False

def get_selenium_status() -> Optional[str]:
    """
    Get the current status of Selenium.

    When SELENIUM_REMOTE_URL is set, returns 'running' or 'unreachable'
    based on a health-check HTTP ping (no Docker SDK needed).
    Otherwise checks the local Docker container status.

    Returns:
        str: Status string or None if not found
    """
    remote_url = _remote_url()
    if remote_url:
        return "running" if _check_remote_selenium(remote_url) else "unreachable"

    try:
        import docker
        from docker.errors import NotFound
        client = docker.from_env()
        container = client.containers.get(CONTAINER_NAME)
        return container.status
    except NotFound:
        return None
    except Exception as e:
        print(f"[!] Error checking status: {e}")
        return None
