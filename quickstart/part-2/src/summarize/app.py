# @@@SNIPSTART quickstart-py-part-2-app
from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)

# Create an instance of Resonate with a remote promise store
resonate = Resonate(store=RemoteStore(url="http://localhost:8001"))


# Define the downloadAndSummarize workflow
# Register it with Resonate as a top-level orchestrating generator
@resonate.register
def downloadAndSummarize(ctx: Context, url: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    content = yield ctx.lfc(download, url)
    print(content)
    # highlight-start
    # Add a delay so you have time to simulate a failure
    time.sleep(10)
    # highlight-end
    # Summarize the downloaded content
    summary = yield ctx.lfc(summarize, url, content)
    print(summary)
    # Return the summary
    return summary


def download(ctx: Context, url: str):
    print(f"Downloading data from {url}")
    time.sleep(2.5)
    # Simulate a failure to download data 50% of the time
    if random.randint(0, 100) > 50:
        print("Download failed")
        raise Exception("Failed to download data")
    print("Download successful")
    return f"This is the content of {url}"


def summarize(ctx: Context, url: str, content: str):
    print("Summarizing content...")
    time.sleep(2.5)
    if random.randint(0, 100) > 50:
        print("Summarization failed")
        raise Exception("Failed to summarize content")
    print("Summarization successful")
    return f"This is the summary of {url}."


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

        # Run the summarize function asynchronously
        promise = downloadAndSummarize.run(id=f"downloadAndSummarize-{url}", url=url)

        # Return the result as JSON
        return jsonify({"summary": promise.result()})
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
