from flask import Flask, request, Response, jsonify
import logging
import requests
import os
import time
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8080))
BACKENDS = os.environ.get("BACKENDS", "").split(",")
HEALTH_INTERVAL = int(os.environ.get("HEALTH_INTERVAL", 5))

class Backend:
    def __init__(self, url):
        self.url = url
        self.healthy = True
        self.last_check = None

class LoadBalancer:
    def __init__(self, backend_urls, health_check_interval=5):
        self.backends = [Backend(url) for url in backend_urls]
        self.health_check_interval = health_check_interval
        self.current_index = 0
        self.lock = threading.Lock()

    def get_next_backend(self):
        with self.lock:
            healthy_backends = [b for b in self.backends if b.healthy]
            if not healthy_backends:
                return None
            self.current_index = self.current_index % len(healthy_backends)
            backend = healthy_backends[self.current_index]
            self.current_index +=1
            return backend

    def check_health(self, backend):
        try:
            logger.info(f"health check for {backend.url}")
            resp = requests.get(f"{backend.url}/health", timeout=2)
            backend.healthy = resp.status_code == 200
        except requests.exceptions.RequestException as e:
            backend.healthy = False
            
        backend.last_check = time.time()
        logger.info("backend : {backend.url} -> healthy: {backend.healthy}")

    def health_check_loop(self):
        while True:
            for backend in self.backends:
                self.check_health(backend)
            time.sleep(self.health_check_interval)

    def start_health_checks(self):
        logger.info("health check loop started")
        thread = threading.Thread(target=self.health_check_loop, daemon=True)
        thread.start()
    

lb = LoadBalancer(BACKENDS, HEALTH_INTERVAL)

@app.route("/")
def proxy():
    backend = lb.get_next_backend()
    logging.info(f"forwarding request to {backend}")

    if not backend:
        return Response("no healthy backends", status=503)
    try:
        resp = requests.request(
            method = request.method,
            url=backend.url,
            headers={k: v for k, v in request.headers if k.lower()!= "host"},    
            data=request.get_data(),
            allow_redirects=False
        )
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))

    except requests.exceptions.RequestException as e:
        logger.error(f"Backend {backend} failed: {e}")
        return Response("backend unavailable", status=502)

@app.route("/lb/status")
def lbstatus():
    return jsonify({
        "backends": [{"url": b.url, "healthy": b.healthy, "last_check": b.last_check} for b in lb.backends]
    })

if __name__ == '__main__':
    logger.info(f"load balancer starting on port {PORT} ")
    logger.info(f"list of backends {BACKENDS}")
    lb.start_health_checks()
    app.run("0.0.0.0", port=PORT)
