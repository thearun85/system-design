from flask import Flask, request, Response
import logging
import itertools
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8080))
BACKENDS = os.environ.get("BACKENDS", "").split(",")
backend_cycle = itertools.cycle(BACKENDS)

def get_next_backend():
    return next(backend_cycle)

@app.route("/")
def proxy():
    backend = get_next_backend()
    logging.info(f"forwarding request to {backend}")

    try:
        resp = requests.request(
            method = request.method,
            url=backend,
            headers={k: v for k, v in request.headers if k.lower()!= "host"},    
            data=request.get_data(),
            allow_redirects=False
        )
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))

    except requests.exceptions.RequestException as e:
        logger.error(f"Backend {backend} failed: {e}")
        return Response("backend unavailable", status=502)

    
if __name__ == '__main__':
    logger.info(f"load balancer starting on port {PORT} ")
    logger.info(f"list of backends {BACKENDS}")
    
    app.run("0.0.0.0", port=PORT)
