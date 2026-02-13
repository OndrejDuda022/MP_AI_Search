"""Cross-platform Docker container management for Selenium"""
import docker
from docker.errors import DockerException, NotFound, APIError
import time
from typing import Tuple, Optional

CONTAINER_NAME = "selenium-chrome"
IMAGE_NAME = "selenium/standalone-chrome:latest"
PORT = "4444"
SELENIUM_URL = f"http://localhost:{PORT}/wd/hub"

def ensure_selenium_container() -> bool:
    """
    Ensure Selenium Docker container is running.
    
    Returns:
        bool: True if container is running, False otherwise
    """
    print("[*] Checking Selenium container...")
    
    try:
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
                return True
            elif container.status == "exited":
                print("[*] Starting existing Selenium container...")
                container.start()
                _wait_for_container(container)
                print("[+] Selenium container started successfully")
                print(f"[*] Container URL: {SELENIUM_URL}")
                return True
            else:
                print(f"[!] Container in unexpected state: {container.status}")
                return False
                
        except NotFound:
            # Container doesn't exist, create it
            print("[*] Creating new Selenium container...")
            return _create_selenium_container(client)
            
    except DockerException as e:
        print(f"[!] Docker error: {e}")
        print("[!] Make sure Docker is installed and running")
        return False
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return False

def _create_selenium_container(client: docker.DockerClient) -> bool:
    """
    Create and start a new Selenium container.
    
    Args:
        client: Docker client instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
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
    Get the current status of the Selenium container.
    
    Returns:
        str: Container status or None if not found
    """
    try:
        client = docker.from_env()
        container = client.containers.get(CONTAINER_NAME)
        return container.status
    except NotFound:
        return None
    except Exception as e:
        print(f"[!] Error checking status: {e}")
        return None
