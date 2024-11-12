# @@@SNIPSTART quickstart-py-part-5-app
from resonate.storage.resonate_server import RemoteServer
from resonate.commands import CreateDurablePromiseReq
from resonate.scheduler import Scheduler
from resonate.context import Context
from selenium import webdriver
from bs4 import BeautifulSoup
import ollama


# Initialize the Resonate Scheduler using the Resonate Server as remote storage
resonate = Scheduler(
    RemoteServer(url="http://localhost:8001"), logic_group="summarization-nodes"
)


# highlight-next-line
def downloadAndSummarize(ctx: Context, url: str, clean_url: str, email: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the provided URL
    # highlight-next-line
    filename = yield ctx.lfc(download, url, clean_url).with_options(durable=False)
    count = 1
    while True:
        # Summarize the downloaded content
        summary = yield ctx.lfc(summarize, url, filename).with_options(
            # highlight-next-line
            promise_id=f"sumarize-{clean_url}-{count}"
        )
        # Send an email with the summary
        yield ctx.lfc(send_email, summary, url, email, count).with_options(
            # highlight-next-line
            promise_id=f"summarization-email-{clean_url}-{count}"
        )
        print("Waiting on confirmation")
        confirmed = yield ctx.rfc(
            CreateDurablePromiseReq(
                # highlight-next-line
                promise_id=f"sumarization-confirmed-{clean_url}-{count}",
            )
        )
        if confirmed:
            break
        count += 1
    print("Workflow completed")
    return


# highlight-next-line
def download(ctx: Context, url: str, clean_url: str):
    print(f"Downloading data from {url}")
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content = soup.get_text()
        filename = f"{clean_url}.txt"
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
