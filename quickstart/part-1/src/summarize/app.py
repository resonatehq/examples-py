# @@@SNIPSTART quickstart-py-part-1-app
from resonate.context import Context
from resonate.resonate import Resonate
from resonate.stores.local import LocalStore, MemoryStorage
import random
import time

# Create a Resonate instance with a local store
resonate = Resonate(store=LocalStore(MemoryStorage()))

# Define and register the downloadAndSummarize function
@resonate.register
def downloadAndSummarize(ctx: Context, url: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    content = yield ctx.lfc(download, url)
    # Summarize the downloaded content
    summary = yield ctx.lfc(summarize, url, content)
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
    # Simulate a failure to summarize content 50% of the time
    if random.randint(0, 100) > 50:
        print("Summarization failed")
        raise Exception("Failed to summarize content")
    print("Summarization successful")
    return f"This is the summary of {url}."


# @@@SNIPEND
