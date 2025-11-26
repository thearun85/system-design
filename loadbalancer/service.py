from flask import Flask, jsonify
import argparse
import socket
from datetime import datetime

app = Flask(__name__)

SERVICE_ID = socket.gethostname()
PORT = None

@app.route("/")
def index():
    return jsonify({
        "service_id": SERVICE_ID,
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001, help="port to access the service")
    parser.add_argument("--id", type=str, default=None, help="an id to identify the service")

    args = parser.parse_args()

    PORT = args.port
    if args.id:
        SERVICE_ID = args.id
        
    app.run("0.0.0.0", port=PORT)
