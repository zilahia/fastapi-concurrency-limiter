# fastapi-concurrency-limiter

Semaphore-based concurrency limiter for [FastAPI](https://fastapi.tiangolo.com/). Define named resources with a maximum concurrency, apply them to routes with a decorator, and get automatic 503 responses when the server is too busy.

## Why

When a shared resource — such as a database or filesystem — receives more concurrent requests than it can handle, its performance degrades. This overload can cascade across the entire application, starving unrelated endpoints of capacity.

The classic solution is rate limiting (e.g. [fastapi-limiter](https://github.com/long2ice/fastapi-limiter)), which caps how many requests an endpoint accepts per unit of time. This library takes a different approach: **concurrency limiting**. Each resource is backed by a semaphore that allows only a fixed number of requests to run simultaneously. Excess requests queue in Python's async runtime rather than being rejected immediately, and a configurable timeout ensures that requests which wait too long are terminated with an HTTP 503 instead of going stale.

### Example with benchmark

The API used for this test has two endpoints:
- `messages` — performs a database query
- `file` — reads from the filesystem

The benchmark is implemented with Grafana k6.

File endpoint:
- 2 virtual users (VUs) continuously hit the `file` endpoint throughout the entire test as a baseline

Messages endpoint:
- 10 VUs loop on the `messages` endpoint to show normal operation
- VU count on `messages` spikes to 150 to simulate overload
- VU count drops back to 10 to observe recovery

#### Without limiting
<img src="https://raw.githubusercontent.com/zilahia/fastapi-concurrency-limiter/main/doc/chart_original.png" width="400" alt="Chart showing results without limiting">

The overloaded `messages` endpoint heavily affects the `file` endpoint. At peak load there are virtually no successful requests from either endpoint, because responses arrive too late for the client. When load drops, the system takes around 10 seconds to recover — stale requests queued during the spike must drain before throughput returns to normal.

#### With limiting
<img src="https://raw.githubusercontent.com/zilahia/fastapi-concurrency-limiter/main/doc/chart_fixed.png" width="400" alt="Chart showing results with limiting">

Even at steady state, performance is better: capping the database to 5 concurrent requests lets it operate more efficiently and use fewer resources, which benefits the `file` endpoint as well. When load spikes, the `file` endpoint is unaffected — system load stays bounded. Excess requests are rejected with HTTP 503 before they can go stale, so the error count stays well below the request count and errors are predictable 503s rather than opaque timeouts. When load returns to normal, throughput recovers immediately because there is no backlog of stale requests.

## Installation

```bash
pip install fastapi-concurrency-limiter
```

## Usage

```python
from fastapi import FastAPI
from fastapi_concurrency_limiter import Limiter, Resource

app = FastAPI()

database_resource = Resource(5)   # max 5 concurrent DB operations
file_resource = Resource(10)      # max 10 concurrent file operations

# Register resources with the limiter in the order they should be acquired.
# Always use this same order in @limiter.resources() to prevent deadlocks.
limiter = Limiter(timeout=5, resources=[database_resource, file_resource])


@app.get("/messages")
@limiter.resources([database_resource])
async def read_messages():
    ...


@app.get("/file")
@limiter.resources([file_resource])
async def read_file():
    ...


@app.get("/messages-and-file")
@limiter.resources([database_resource, file_resource])  # must match registration order
async def read_messages_and_file():
    ...
```

When a request cannot acquire a semaphore within `timeout` seconds it receives:

```json
{"detail": "Server busy, please retry later"}
```

with HTTP status **503**.

## Resource ordering and deadlocks

When an endpoint acquires multiple resources, always pass them to `@limiter.resources()` in the same order they were registered in `Limiter(resources=[...])`. Passing them in a different order raises a `ValueError` at startup — this is intentional: consistent acquisition order is the simplest way to prevent deadlocks.

```python
limiter = Limiter(timeout=5, resources=[db, fs])

@app.get("/ok")
@limiter.resources([db, fs])   # correct
async def ok(): ...

@app.get("/bad")
@limiter.resources([fs, db])   # raises ValueError at startup
async def bad(): ...
```

## API

### `Resource(capacity: int)`

A semaphore with the given concurrency limit.

### `Limiter(timeout: float, resources: list[Resource])`

- `timeout` — seconds to wait for semaphore acquisition before returning 503.
- `resources` — all resources managed by this limiter, in canonical acquisition order.

### `@limiter.resources(resources: list[Resource])`

Route decorator. Acquires the listed resources before the handler runs and releases them after, even on exception.

## License

MIT
