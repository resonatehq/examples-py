# Part 1 example application

**Python quickstart tutorial | Incremental adoption**

This example application is meant to showcase Resonate's incremental adoption value proposition and work with the content in the first part of the [Python SDK quickstart tutorial](https://docs.resonatehq.io/get-started/python-quickstart#part-1-incremental-adoption).

This example is set up using [Rye](https://rye.astral.sh/) as the environment and package manager.

Check the `pyproject.toml` file to see which version of the Python SDK is being used.

**Terminal 1:**

```shell
rye sync
rye run app
```

**Terminal 2:**

From another terminal send a cURL request:

```shell
curl -X POST http://localhost:5000/summarize -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
```
