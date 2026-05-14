from flask import Flask, jsonify
import os

app = Flask(__name__)


@app.route('/')
def home():
    import main as _m
    return jsonify({
        "status": "online",
        "service": "Premium Hosting Bot v1",
        "projects": len(_m.project_owners),
        "running": len([p for p in _m.running_processes.values() if p.poll() is None]),
        "recovery": _m.recovery_enabled,
        "live_logs": _m.live_logs_enabled
    })


@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200


def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
