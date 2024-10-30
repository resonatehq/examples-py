from flask import Flask, jsonify, request
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage import RemoteServer

app = Flask(__name__)
resonate = Scheduler(RemoteServer(url="http://localhost:8001"))


def workflow(ctx: Context, email: str):
    promise = yield ctx.rfi("notify_human", email)
    confirmation = yield promise
    return confirmation


resonate.register(workflow)


@app.route("/start", methods=["POST"])
def start_workflow_route_handler():
    try:
        data = request.get_json()
        if "email" not in data:
            return jsonify({"error": "email is required"}), 400
        email = data["email"]

        promise = resonate.run("workflow", workflow, email).result()
        return jsonify({"confirmation": promise.result()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main() -> None:
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
