# @@@SNIPSTART quickstart-py-part-5-gateway
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
from resonate.targets import poll
from flask import Flask, request, jsonify
import json
import re

app = Flask(__name__)

# Create a Resonate Scheduler
store = RemoteStore(url="http://localhost:8001")
resonate = Resonate(
    store=store, task_source=Poller(url="http://localhost:8002", group="gateway")
)


@resonate.register
def dispatch(ctx: Context, url: str, clean_url: str, email: str):
    yield ctx.rfi("downloadAndSummarize", url, clean_url, email).options(
        send_to=poll("summarization-nodes")
    )
    return


# Define a route handler for the /summarize endpoint
@app.route("/summarize", methods=["POST"])
def summarize_route_handler():
    try:
        # Extract JSON data from the request
        data = request.get_json()
        if "url" not in data:
            return jsonify({"error": "URL not provided"}), 400

        # Extract the URL from the request
        url = data["url"]
        email = data["email"]
        # highlight-next-line
        clean_url = clean(url)

        # Use a Remote Function Invocation
        dispatch.run(f"downloadAndSummarize-{clean_url}", url, clean_url, email)

        # Return the result as JSON
        return jsonify({"summary": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/confirm", methods=["GET"])
def confirm_email_route_handler():
    global store
    try:
        url = request.args.get("url")
        confirm = request.args.get("confirm")
        attempt = request.args.get("attempt")
        # Check if the required parameters are present
        if not url or confirm is None or attempt is None:
            return jsonify({"error": "url and confirmation params are required"}), 400
        # Parse parameters
        confirm = confirm.lower() == "true"
        # highlight-next-line
        clean_url = clean(url)
        # Resolve the promise
        store.promises.resolve(
            id=f"sumarization-confirmed-{clean_url}-{attempt}",
            ikey=None,
            strict=False,
            headers=None,
            data=json.dumps(confirm),
        )
        if confirm:
            return jsonify({"message": "Summarization confirmed."}), 200
        else:
            return jsonify({"message": "Summarization rejected."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def clean(url):
    tmp = re.sub(r"^https?://", "", url)
    return tmp.replace("/", "-")


# Define a main function to start the Flask app
def main():
    app.run(host="127.0.0.1", port=5000)
    print("Serving HTTP on port 5000...")


# Run the main function when the script is executed
if __name__ == "__main__":
    main()

# @@@SNIPEND
