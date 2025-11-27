import subprocess
import requests
import sys
import time
import os

YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"

PASSED = 0
FAILED = 0

LB_URL = "http://localhost:8080"
BACKEND_PORTS = [5001,5002,5003]
BACKEND_NAMES = ["backend-1","backend-2","backend-3"]

def log_pass(msg):
    global PASSED
    print(f"{GREEN}\u2713[PASS]{NC} {msg}")
    PASSED +=1

def log_fail(msg):
    global FAILED
    print(f"{RED}\u2717[FAIL]{NC} {msg}")
    FAILED +=1

def log_info(msg):
    print(f"{YELLOW}[INFO]{NC} {msg}")

def log_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")

def run(cmd):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            log_error(f"Command failed: {cmd}")
            if result.stdout:
                log_error(f"stdout: {result.stdout.strip()}")
            if result.stderr:
                log_error(f"stderr: {result.stderr.strip()}")
        return result

    except Exception as e:
        log_error(f"exception occurred : {e}")
        return None

def wait_for_service(url, max_attempts=30):
    for attempt in range(max_attempts):
        try:
            requests.get(url, timeout=1)
            return True
        except requests.exceptions.RequestException as e:
            time.sleep(1)
    return False

def setup():
    log_info("Stopping any existing containers")
    result = run("docker compose down -v")
    if result is None:
        return False

    log_info("Building and starting containers")  
    result = run("docker compose up -d --build")
    if result is None or result.returncode != 0:
        log_fail("Failed to start containers")
        run("docker compose logs", show_output=True)
        return False

    log_info("Waiting for load balancer")
    if wait_for_service(LB_URL):
        log_pass("Load balancer is responding")
        return True
    else:
        log_fail("Load balancer failed to start")
        run("docker compose logs loadbalancer", show_output=True)
        return False

def teardown():
    log_info("Cleaning up")
    run("docker compose down -v")

def print_summary():
    print("")
    print("=" * 40)
    print(f"Tests passed: {GREEN}{PASSED}{NC}")
    print(f"Tests failed: {RED}{FAILED}{NC}")
    print("=" * 40)

def test_backends_direct():
    log_info("Testing direct backend access")
    for i, port in enumerate(BACKEND_PORTS):
        url = f"http://localhost:{port}"

        try:
            resp = requests.get(url, timeout=2)
            data = resp.json()

            if resp.status_code == 200:
                log_pass(f"Backend on port {port} responded with data : {data}")
            else:
                log_fail(f"Backend on port {port} failed with data {data}")
        except Exception as e:
            log_fail("Backend on port {port} error : {e}")

def test_lb_status():
    log_info("Testing load balancer status api point")

    try:
        resp = requests.get(f"{LB_URL}/lb/status", timeout=2)
        if resp.status_code != 200:
            log_fail("/lb/status api call failed")
            return None
        data = resp.json()
        log_info(f"/lb/status response is {data}")
        print(f"DEBUG: 'backends' in data = {'backends' in data}")
        
        if "backends" not in data:
            log_error("/lb/status response is {data}")
            log_fail("/lb/status missing 'backends' key")
            return None
        if len(data['backends']) != len(BACKEND_NAMES):
            log_fail("/lb/status does not show all backends records")
            return None

        log_pass("/lb/status call is success")
        return data
    except Exception as e:
        log_fail(f"/lb/status failed with error :{e}")
        return None

def test_all_healthy(status_data):
    log_info("Testing all backends are marked as healthy ")      

    if not status_data:
        log_fail("no status data to check")
        return None

    backends = status_data['backends']
    healthy_count = [1 for b in backends if b["healthy"]]
    if len(backends) != len(healthy_count):
        log_fail(f"Only {len(healthy_count)} backends are healthy out of {len(backends)}")
    log_pass("All backends are healthy")
    return True

def test_round_robin():
    log_info("Tetsing simple round robin lb")
    counts = {}
    for i in range(6):
        resp = requests.get(LB_URL, timeout=2)
        data = resp.json()
        service_id = data.get("service_id")
        counts[service_id] = counts.get(service_id, 0) +1

    if len(counts) != 3:
        log_fail(f"Only {len(counts)} backends received traffic")
    else:
        log_pass("round robin passed")

def test_health_check():
    log_info("Test health check by bringing down backend-2")
    run('docker compose stop backend-2')
    
    time.sleep(int(os.environ.get("HEALTH_INTERVAL", 5)))
    try:
        resp = requests.get(f"{LB_URL}/lb/status", timeout=2)
        data = resp.json()
        if "backends" not in data:
            log_fail("lb/status api call failed after shutting down backend-2")
            return None
        backends = data['backends']
        if len(backends) != len(BACKEND_NAMES):
            log_fail("/lb/status does not show all backends records")
        healthy_backends = sum(1 for b in backends if b["healthy"])
        if healthy_backends == 2:
            log_pass("Health check detected one backend down")
        else:
            log_fail(f"Expected 2 backends got {healthy_backends}")
            return None
        return True
    except Exception as e:
        log_fail(f"Health check failed with : {e}")
        return None

def test_traffic_avoid_unhealthy():
    log_info("Test whether traffic reaches stopped backend-2")
    try:
        for i in range(6):
            resp = requests.get(LB_URL, timeout=2)
            data = resp.json()
            if data.get("service_id") == "backend-2":
                log_fail("Traffic reached unhealthy backend")
                return False
    except Exception as e:
        log_fail(f"test_traffic_avoid_unhealthy failed with : {e}")
        return False
    log_pass("Traffic does not reach unhealthy backend")
    return True

def test_backend_recovery():
    log_info("Test backend-2 recovers after restart")
    run("docker compose start backend-2")
    time.sleep(int(os.environ.get("HEALTH_INTERVAL", 5)))
    try:
        resp = requests.get(f"{LB_URL}/lb/status", timeout=2)
        data = resp.json()
        backends = data['backends']
        healthy_count = sum(1 for b in backends if b['healthy'])
        if healthy_count == 3:
            log_pass("Backend-2 is restarted sucecsfully and available")
            return True
        else:
            log_fail("restarted backend isnt available to serve")
            return False
    except Exception as e:
        log_fail(f"test_backend_recovery failed with {e}")
        return False
            
    
def main():
    try:
        if not setup():
            teardown()
            sys.exit(1)

        test_backends_direct()
        lb_status = test_lb_status()
        test_all_healthy(lb_status)
        test_round_robin()
        test_health_check()
        test_traffic_avoid_unhealthy()
        test_backend_recovery()
    except KeyboardInterrupt:
        log_info("Interrupted by user")
    except Exception as e:
        log_error(f"unexpected error: {e}")
    finally:
        teardown()

    print_summary()
    sys.exit(0 if FAILED == 0 else 1)

if __name__ == '__main__':
    main()
