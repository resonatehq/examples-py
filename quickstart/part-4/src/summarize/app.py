# @@@SNIPSTART quickstart-py-part-4-app
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate.commands import DurablePromise
from resonate.resonate import Resonate
from resonate.context import Context
from threading import Event
import random
import time

resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    task_source=Poller(url="http://localhost:8002", group="summarization-nodes"),
)


# Define and register the downloadAndSummarize workflow
@resonate.register
def downloadAndSummarize(ctx: Context, url: str, email: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    content = yield ctx.lfc(download, url)
    # Loop until the summary is confirmed
    while True:
        # Summarize the downloaded content
        summary = yield ctx.lfc(summarize, url, content)

        # Create a Durable Promise to wait for confirmation
        promise = yield ctx.rfi(DurablePromise(id=None))

        # Send an email with the summary
        yield ctx.lfc(send_email, summary, email, promise.id)

        # Wait for the summary to be accepted or rejected
        print("Waiting on confirmation")
        confirmed = yield promise

        if confirmed:
            break

    print("Workflow complete")
    return


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


def send_email(ctx: Context, summary: str, email: str, promise_id: str):
    print(f"Summary: {summary}")
    print(
        f"Click to confirm: http://localhost:5000/confirm?confirm=true&promise_id={promise_id}"
    )
    print(
        f"Click to reject: http://localhost:5000/confirm?confirm=false&promise_id={promise_id}"
    )
    print("Email sent successfully")
    return


# Define a main function to start the Application Node
def main():
    print("App node running")
    Event().wait()


# Run the main function when the script is executed
if __name__ == "__main__":
    main()

# @@@SNIPEND
