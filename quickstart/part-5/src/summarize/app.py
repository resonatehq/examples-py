# @@@SNIPSTART quickstart-py-part-5-app
from resonate.commands import DurablePromise
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate.resonate import Resonate
from resonate.context import Context
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Event
import ollama
import os


# Initialize the Resonate Scheduler using the Resonate Server as remote storage
resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    task_source=Poller(url="http://localhost:8002", group="summarization-nodes"),
)


# highlight-next-line
@resonate.register
def downloadAndSummarize(ctx: Context, url: str, clean_url: str, email: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    # highlight-next-line
    filename = yield ctx.lfc(download, url, clean_url).options(durable=False)
    while True:
        # Summarize the downloaded content
        summary = yield ctx.lfc(summarize, url, filename)

        # Create a DurablePromise to wait for the confirmation
        promise = yield ctx.rfi(DurablePromise(id=None))

        # Send an email with the summary
        yield ctx.lfc(send_email, summary, email, promise.id)

        # Wait for the summary to be accepted or rejected
        print("Waiting on confirmation")
        confirmed = yield promise

        if confirmed:
            break

    print("Workflow completed")
    return


# highlight-next-line
def download(ctx: Context, url: str, clean_url: str):
    filename = f"{clean_url}.txt"

    # Check if the file already exists
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return filename

    print(f"Downloading data from {url}")
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content = soup.get_text()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        driver.quit()
        print(f"Content saved to {filename}")
        return filename
    except Exception as e:
        print(f"Download failed: {e}")
        raise Exception(f"Failed to download data: {e}")


def summarize(ctx: Context, url: str, filename: str):
    print(f"Summarizing content from {url}")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file_content = f.read()

        options: ollama.Options | None = None

        summary = ollama.chat(
            model="llama3.1",
            messages=[
                {
                    "role": "system",
                    "content": "You review text scraped from a website and summarize it. Ignore text that does not support the narrative and purpose of the website.",
                },
                {"role": "user", "content": f"Content to summarize: {file_content}"},
            ],
            options=options,
        )
        return summary
    except Exception as e:
        print(f"Summarization failed: {e}")
        raise Exception(f"Failed to summarize content: {e}")


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
