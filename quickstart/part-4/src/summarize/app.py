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
    # Add a delay so you have time to simulate a failure
    time.sleep(10)
    count = 1
    while True:
        # Summarize the downloaded content
        summary = yield ctx.lfc(summarize, url, content).with_options(
            promise_id=f"sumarize-{url}-{count}"
        )
        # Send an email with the summary
        yield ctx.lfc(send_email, summary, url, email, count).with_options(
            promise_id=f"summarization-email-{url}-{count}"
        )
        print("Waiting on confirmation")
        confirmed = yield ctx.rfc(
            DurablePromise(
                promise_id=f"sumarization-confirmed-{url}-{count}",
            )
        )
        if confirmed:
            break
        count += 1
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


def send_email(ctx: Context, summary: str, url: str, email: str, attempt: int):
    print(f"Summary: {summary}")
    print(
        f"Click to confirm: http://localhost:5000/confirm?url={url}&confirm=true&attempt={attempt}"
    )
    print(
        f"Click to reject: http://localhost:5000/confirm?url={url}&confirm=false&attempt={attempt}"
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
