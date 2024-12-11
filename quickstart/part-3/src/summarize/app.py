# @@@SNIPSTART quickstart-py-part-3-app
#highlight-next-line
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
# highlight-next-line
from threading import Event
import random
import time

resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    # highlight-next-line
    task_source=Poller(url="http://localhost:8002", group="summarization-nodes"),
)


# Define and register the downloadAndSummarize workflow
@resonate.register
def downloadAndSummarize(ctx: Context, url: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    content = yield ctx.lfc(download, url)
    print(content)
    # Add a delay so you have time to simulate a failure
    time.sleep(10)
    # Summarize the downloaded content
    summary = yield ctx.lfc(summarize, url, content)
    print(summary)
    # Return the summary
    return summary


def download(ctx: Context, url: str):
    print(f"Downloading data from {url}")
    time.sleep(random.randint(1, 5))
    # Simulate a failure to download data 50% of the time
    if random.randint(0, 100) > 50:
        print("Download failed")
        raise Exception("Failed to download data")
    print("Download successful")
    return f"This is the content of {url}"


def summarize(ctx: Context, url: str, content: str):
    print("Summarizing content...")
    time.sleep(random.randint(1, 5))
    if random.randint(0, 100) > 50:
        print("Summarization failed")
        raise Exception("Failed to summarize content")
    print("Summarization successful")
    return f"This is the summary of {url}."


# Define a main function to start the Application Node
def main():
    print("App node running")
    # highlight-next-line
    Event().wait()


# Run the main function when the script is executed
if __name__ == "__main__":
    main()

# @@@SNIPEND
