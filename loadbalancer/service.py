from flask import Flask, jsonify
import socket
from datetime import datetime
import os

app = Flask(__name__)

SERVICE_ID = os.environ.get("SERVICE_ID", socket.gethostname())
PORT = int(os.environ.get("PORT", 5000))

@app.route("/")
def index():
    return jsonify({
        "service_id": SERVICE_ID,
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })

if __name__ == '__main__':
    app.run("0.0.0.0", port=PORT)
