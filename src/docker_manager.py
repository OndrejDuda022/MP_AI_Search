import os
import time
from typing import Optional

CONTAINER_NAME = "selenium-chrome"
IMAGE_NAME = "selenium/standalone-chrome:latest"
PORT = "4444"
SELENIUM_URL = f"http://localhost:{PORT}/wd/hub"


# Check whether the current process is running inside a Docker container
# Parameters: none
# Returns: bool - True if running inside a container, False otherwise
def is_running_in_container() -> bool:
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


# Read the remote Selenium URL from environment, if configured
# Parameters: none
# Returns: Optional[str] - URL string or None if not set
def _remote_url() -> Optional[str]:
    url = os.getenv("SELENIUM_REMOTE_URL", "").strip()
    return url if url else None


# Verify that a remote Selenium server is reachable and responding
# Parameters: remote_url (str) - base URL of the remote Selenium hub
# Returns: bool - True if the server returns HTTP 200, False otherwise
def _check_remote_selenium(remote_url: str) -> bool:
    import requests
    try:
        status_url = remote_url.replace("/wd/hub", "/status")
        response = requests.get(status_url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# Poll the local Selenium container until it is ready or timeout is reached
# Parameters: max_wait (int) - maximum seconds to wait
# Returns: bool - True if Selenium became ready in time, False on timeout
def _wait_for_selenium(max_wait: int = 30) -> bool:
    import requests
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(f"{SELENIUM_URL}/status", timeout=2)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    print("[!] Timeout waiting for Selenium to be ready")
    return False


# Ensure the Selenium container (local Docker or remote) is running and ready
# Starts or creates the container when necessary and sets SELENIUM_REMOTE_URL
# Parameters: none
# Returns: bool - True if Selenium is available, False if it could not be started
def ensure_selenium_container() -> bool:
    os.environ.pop("SELENIUM_REMOTE_URL", None)

    if is_running_in_container():
        target = _remote_url() or SELENIUM_URL
        print(f"[*] Checking remote Selenium at {target}...")
        if _check_remote_selenium(target):
            os.environ["SELENIUM_REMOTE_URL"] = target
            print("[+] Remote Selenium is ready")
            return True
        print("[!] Remote Selenium is not reachable")
        return False

    print("[*] Checking Selenium container (local Docker)...")

    try:
        import docker
        from docker.errors import DockerException, NotFound, APIError
    except ImportError:
        print("[!] Docker SDK not installed. Install it with: pip install docker>=6.0.0")
        return False

    try:
        client = docker.from_env()
        client.ping()
    except DockerException as e:
        print(f"[!] Docker is not running or not accessible: {e}")
        return False
    except Exception as e:
        print(f"[!] Could not connect to Docker: {e}")
        return False

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
        else:
            print(f"[!] Container in unexpected state: {container.status}")
            return False
    except NotFound:
        print("[*] Creating new Selenium container...")
        try:
            client.images.get(IMAGE_NAME)
            print("[*] Using existing Selenium image")
        except docker.errors.ImageNotFound:
            print("[*] Pulling Selenium image (this may take a few minutes)...")
            client.images.pull(IMAGE_NAME)
            print("[+] Image pulled successfully")
        try:
            client.containers.run(
                IMAGE_NAME,
                name=CONTAINER_NAME,
                ports={"4444/tcp": PORT},
                detach=True,
                shm_size="2g",
                remove=False,
            )
        except APIError as e:
            print(f"[!] Failed to create container: {e}")
            return False
    except Exception as e:
        print(f"[!] Unexpected error managing Selenium container: {e}")
        return False

    print("[*] Waiting for Selenium to be ready...")
    if _wait_for_selenium():
        print("[+] Selenium container started successfully")
        print(f"[*] Container URL: {SELENIUM_URL}")
        os.environ["SELENIUM_REMOTE_URL"] = SELENIUM_URL
        return True
    print("[!] Selenium did not become ready in time")
    return False


# Stop the local Selenium Docker container gracefully
# Parameters: none
# Returns: bool - True if stopped successfully or already stopped, False on error
def stop_selenium_container() -> bool:
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
        print(f"[!] Failed to stop container: {e}")
        return False
