# @@@SNIPSTART quickstart-py-part-3-gateway
# highlight-next-line
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
# highlight-next-line
from resonate.targets import poll
from flask import Flask, request, jsonify


app = Flask(__name__)

# Create an instance of Resonate
resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    # highlight-next-line
    task_source=Poller(url="http://localhost:8002", group="gateway"),
)

# highlight-start
# Define and register a top-level orchestrator coroutine
@resonate.register
def dispatch(ctx: Context, url: str):
    yield ctx.rfi("downloadAndSummarize", url).options(
        send_to=poll("summarization-nodes")
    )
    return
# highlight-end

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

        # highlight-next-line
        dispatch.run(id=f"downloadAndSummarize-{url}", url=url)

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
