from flask import Flask, jsonify, request
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage import RemoteServer
import time

app = Flask(__name__)
resonate = Scheduler(RemoteServer(url="http://localhost:8001"))

confirmed = False


def notify_human(ctx: Context, email: str):
    while not confirmed:
        print(f"Waiting on human to confirm {email}")
        time.sleep(10)
    return confirmed


resonate.register(notify_human)


@app.route("/confirm", methods=["POST"])
def start_workflow_route_handler():
    try:
        data = request.get_json()
        if "confirm" not in data:
            return jsonify({"error": "confirm param is required"}), 400
        confirmed = data["confirm"]

        return jsonify({"your confirmation value": confirmed}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main() -> None:
    app.run(host="0.0.0.0", port=5001)


if __name__ == "__main__":
    main()
