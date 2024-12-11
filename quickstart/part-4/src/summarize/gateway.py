from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
from resonate.targets import poll
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Create a Resonate Scheduler
store = RemoteStore(url="http://localhost:8001")
resonate = Resonate(store=store)


# Define and register a top-level orchestrating coroutine
@resonate.register
def dispatch(ctx: Context, url: str, email: str):
    yield ctx.rfi("downloadAndSummarize", url, email).options(
        send_to=poll("summarization-nodes")
    )
    return


# @@@SNIPSTART quickstart-py-part-4-gateway-summarize-route
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
        # highlight-next-line
        email = data["email"]

        dispatch.run(f"downloadAndSummarize-{url}", url, email)

        # Return the result as JSON
        return jsonify({"summary": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @@@SNIPEND


# @@@SNIPSTART quickstart-py-part-4-gateway-confirm-route
@app.route("/confirm", methods=["GET"])
def confirm_email_route_handler():
    global store
    try:
        # Extract parameters from the request
        promise_id = request.args.get("promise_id")
        confirm = request.args.get("confirm")
    
        # Check if the required parameters are present
        if not promise_id or confirm is None:
            return jsonify({"error": "url and confirmation params are required"}), 400
        
        # Convert to boolean
        confirm = confirm.lower() == "true"

        # Resolve the promise
        store.resolve(
            id=promise_id,
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


# @@@SNIPEND


# Define a main function to start the Flask app
def main():
    app.run(host="127.0.0.1", port=5000)
    print("Serving HTTP on port 5000...")


# Run the main function when the script is executed
if __name__ == "__main__":
    main()
