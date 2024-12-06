from flask import Flask, request, jsonify
from summarize.app import downloadAndSummarize

app = Flask(__name__)


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
