from resonate.storage.resonate_server import RemoteServer
from resonate.scheduler import Scheduler
from flask import Flask, jsonify, request
import json

app = Flask(__name__)
store = RemoteServer(url="http://localhost:8001")
resonate = Scheduler(store)


@app.route("/start", methods=["POST"])
def start_workflow_route_handler():
    try:
        data = request.get_json()
        if "email" not in data:
            return jsonify({"error": "email is required"}), 400
        email = data["email"]
        resonate.rfi(
            promise_id=f"workflow-{email}",
            func_name="workflow",
            args=[email],
            target="workflow-service",
        )
        return jsonify({"result": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/confirm", methods=["POST"])
def confirm_email_route_handler():
    global store
    try:
        data = request.get_json()
        if "email" not in data:
            return jsonify({"error": "email param is required"}), 400
        email = data["email"]
        store.resolve(
            promise_id=f"email-confirmed-{email}",
            ikey=None,
            strict=False,
            headers=None,
            data=json.dumps(True),
        )
        return jsonify({"message": f"Email {email} confirmed."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main() -> None:
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
