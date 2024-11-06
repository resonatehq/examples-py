# @@@SNIPSTART quickstart-py-part-4-app
from resonate.storage.resonate_server import RemoteServer
from resonate.scheduler import Scheduler
from resonate.context import Context
import random
import time

resonate = Scheduler(
    RemoteServer(url="http://localhost:8001"), logic_group="summarization-nodes"
)


def downloadAndSummarize(ctx: Context, url: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    content = yield ctx.lfc(download, url).with_options(durable=False)
    print(content)
    # Add a delay so you have time to simulate a failure
    time.sleep(10)
    # Summarize the downloaded content
    summary = yield ctx.lfc(summarize, url, content).with_options(durable=False)
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


resonate.register(
    name="downloadAndSummarize",
    func=downloadAndSummarize,
)


# Define a main function to start the Application Node
def main():
    print("App node running")
    resonate.wait_forever()


# Run the main function when the script is executed
if __name__ == "__main__":
    main()

# @@@SNIPEND