# Part 2 example application

**Python quickstart tutorial | Durable Execution**

This example application is meant to showcase Resonate's Durable Execution value proposition and work with the content in the second part of the [Python SDK quickstart tutorial](https://docs.resonatehq.io/get-started/python-quickstart#part-2-durable-execution).

This example is set up using [Rye](https://rye.astral.sh/) as the environment and package manager.

This example requires that the [Resonate Server is running locally](https://docs.resonatehq.io/get-started/server-quickstart).

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

You can now kill the application in between steps and watch it resume after bringing it back up.
