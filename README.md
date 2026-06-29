# fastapi-concurrency-limiter

Semaphore-based concurrency limiter for [FastAPI](https://fastapi.tiangolo.com/). Define named resources with a maximum concurrency, apply them to routes with a decorator, and get automatic 503 responses when the server is too busy.

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
