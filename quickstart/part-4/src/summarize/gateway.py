# @@@SNIPSTART quickstart-py-part-4-gateway
from flask import Flask, request, jsonify
from resonate.scheduler import Scheduler
from resonate.storage.resonate_server import RemoteServer
import json

app = Flask(__name__)

# Create a Resonate Scheduler
store = RemoteServer(url="http://localhost:8001")
resonate = Scheduler(store)


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

        # Use a Remote Function Invocation
        resonate.rfi(
            promise_id=f"downloadAndSummarize-{url}",
            func_name="downloadAndSummarize",
            args=[url, email],
            target="summarization-nodes",
        )

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
        # Resolve the promise
        store.resolve(
            promise_id=f"sumarization-confirmed-{url}-{attempt}",
            ikey=None,
            strict=False,
            headers=None,
            data=json.dumps(confirm),
        )
        if confirm:
            return jsonify({"message": f"Summarization confirmed."}), 200
        else:
            return jsonify({"message": f"Summarization rejected."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Define a main function to start the Flask app
def main():
    app.run(host="127.0.0.1", port=5000)
    print("Serving HTTP on port 5000...")


# Run the main function when the script is executed
if __name__ == "__main__":
    main()

# @@@SNIPEND
