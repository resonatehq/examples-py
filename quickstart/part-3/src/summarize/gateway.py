# @@@SNIPSTART quickstart-py-part-3-gateway
from flask import Flask, request, jsonify
from resonate.scheduler import Scheduler
from resonate.storage.resonate_server import RemoteServer

app = Flask(__name__)

# Create a Resonate Scheduler
resonate = Scheduler(durable_promise_storage=RemoteServer(url="http://localhost:8001"))


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

        # Use a Remote Function Invocation
        resonate.rfi(
            promise_id=f"downloadAndSummarize-{url}",
            func_name="downloadAndSummarize",
            args=[url],
            target="summarization-nodes",
        )

        # Return the result as JSON
        return jsonify({"summary": "workflow started"}), 200
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
