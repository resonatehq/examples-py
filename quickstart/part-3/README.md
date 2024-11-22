# Part 3 example application

**Python quickstart tutorial | Fan-out/Fan-in**

This example application is meant to showcase Resonate's Fan-out/Fan-in value proposition and work with the content in the third part of the [Python SDK quickstart tutorial](https://docs.resonatehq.io/get-started/python-quickstart#part-3-fan-outfan-in).

This example is set up using [Rye](https://rye.astral.sh/) as the environment and package manager.

This example requires that the [Resonate Server is running locally](https://docs.resonatehq.io/get-started/server-quickstart).

**Terminal 1:**

```shell
rye sync
rye run gateway
```

**Terminal 2:**

```shell
rye run app
```

You can run as many Application Nodes as you want.

**Terminal 3:**

```shell
rye run app
```

**Terminal 4:**

From another terminal send a cURL request:

```shell
curl -X POST http://localhost:5000/summarize -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
```

You can send many cURL requests for different URLs and watch the different Application Nodes pick up the work.
You can kill an Application Node and see the work resume on the other one.
