from flask import Flask, request, Response
import argparse
import logging
import itertools
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

PORT = None
BACKENDS = []


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

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5010, help="port for the load balancer")
    parser.add_argument("--backends", type=str, required=True, help="comma seperated list of urls")

    args = parser.parse_args()

    PORT = args.port
    BACKENDS = [ b.strip() for b in args.backends.split(',')]
    backend_cycle = itertools.cycle(BACKENDS)

    logger.info(f"load balancer starting on port {PORT} ")
    logger.info(f"list of backends {BACKENDS}")
    
    app.run("0.0.0.0", port=PORT)
