from flask import Flask, jsonify, request
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage.resonate_server import RemoteServer
from resonate.commands import CreateDurablePromiseReq

app = Flask(__name__)
resonate = Scheduler(
    RemoteServer(url="http://localhost:8001"), logic_group="workflow-service"
)


def step3(ctx: Context):
    print("Next step in the process")


def workflow(ctx: Context, email: str):
    # Step 1 - send email with a link to confirm
    yield ctx.rfc(
        CreateDurablePromiseReq(
            promise_id=f"send-confirmation-email-{email}",
            data={"func": "send_email", "args": [email], "kwargs": {}},
            headers=None,
            tags={"resonate:invoke": "poll://email-service"},
        )
    )
    print(f"Email sent to {email}")

    # Step 2 - wait on human input
    confirmation = yield ctx.rfc(
        CreateDurablePromiseReq(
            promise_id=f"email-confirmed-{email}",
        )
    )
    print(f"Email address {email} confirmed: {confirmation}")

    # Step 3
    yield ctx.lfc(step3)

    # Add as many steps as needed

    return


resonate.register(name="workflow", func=workflow)


@app.route("/start", methods=["POST"])
def start_workflow_route_handler():
    try:
        data = request.get_json()
        if "email" not in data:
            return jsonify({"error": "email is required"}), 400
        email = data["email"]
        resonate.run(f"workflow-{email}", workflow, email)
        return jsonify({"result": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main() -> None:
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
