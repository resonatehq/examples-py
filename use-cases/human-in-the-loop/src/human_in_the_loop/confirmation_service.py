from flask import Flask, jsonify, request
from resonate.scheduler import Scheduler

# from resonate.context import Context
from resonate.storage.resonate_server import RemoteServer

# import time
import json

app = Flask(__name__)
store = RemoteServer(url="http://localhost:8001")
resonate = Scheduler(store)

# emails = []
# run = True


# def confirm_email(ctx: Context, email: str):
#     confirmed = False
#     while run:
#         print(f"Waiting on human to confirm {email}")
#         for e in emails:
#             if e == email:
#                 print(f"Email {email} has been confirmed")
#                 confirmed = True
#                 break # Exit the for loop when email is confirmed
#         if confirmed:
#             break  # Exit the while loop when confirmed is True
#         time.sleep(10)
#     return confirmed


# resonate.register(confirm_email)


@app.route("/confirm", methods=["POST"])
def start_workflow_route_handler():
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
    app.run(host="0.0.0.0", port=5001)


if __name__ == "__main__":
    main()
