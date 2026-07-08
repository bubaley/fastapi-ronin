---
title: FastAPI Ronin Cache — In-Memory and Redis Cache
description: Use FastAPI Ronin cache with in-memory or Redis backends, TTL, namespaces, lifespan initialization, and async API methods.
keywords: FastAPI cache, Redis cache, in-memory cache, FastAPI Ronin, TTL, async cache, Python cache
---

# Cache

FastAPI Ronin includes a small async cache client for application code, custom
actions, dependencies, services, and tests.

The cache supports two backends:

- In-memory cache for development, tests, and single-process apps.
- Redis cache for shared cache across processes and deployments.

## Initialize Cache

Initialize the global cache client during FastAPI lifespan and close it on
shutdown.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_ronin.cache import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.init(None)
    yield
    await cache.close()


app = FastAPI(lifespan=lifespan)
```

Calling cache methods before `cache.init()` raises a `RuntimeError`. This makes
missing startup wiring visible during development.

## In-Memory Backend

Use the in-memory backend by passing `None` or omitting `redis_url`.

```python
await cache.init(None)
```

In-memory cache stores values inside the current Python process. It is fast and
simple, but each process has its own store. Use it for local development,
tests, or non-critical per-process values.

## Redis Backend

Install Redis support:

```bash
uv add "fastapi-ronin[redis]"
```

Then initialize cache with a Redis URL:

```python
await cache.init(redis_url='redis://localhost:6379/0')
```

Redis values are JSON serialized. Store JSON-compatible data such as strings,
numbers, booleans, lists, dictionaries, and `None`.

## Basic API

```python
await cache.set('company:stats', {'total': 10}, ttl=60)
stats = await cache.get('company:stats')

exists_count = await cache.exists('company:stats')
await cache.delete('company:stats')

is_alive = await cache.ping()
await cache.clear()
```

| Method | Description |
|--------|-------------|
| `get(key)` | Return cached value or `None`. |
| `set(key, value, ttl=NOT_SET)` | Store a value. |
| `delete(key)` | Remove one key. |
| `exists(*keys)` | Return the number of existing keys. |
| `clear()` | Clear keys for the configured namespace. |
| `ping()` | Check backend health. |
| `close()` | Close backend resources. |

## TTL

Set `default_ttl` during initialization to apply a default expiration:

```python
await cache.init(None, default_ttl=300)
```

Override TTL per value:

```python
await cache.set('short-lived', 'value', ttl=10)
await cache.set('no-expiry', 'value', ttl=None)
```

TTL must be a positive integer or float. Passing `0` or a negative value raises
`ValueError`.

## Namespaces

Cache keys are prefixed with a namespace. The default namespace is
`fastapi_ronin`.

```python
await cache.init(None, namespace='my_api')
await cache.set('stats', {'total': 1})
```

The real backend key becomes `my_api:stats`. `clear()` only removes keys in the
current namespace.

## Use in a ViewSet Action

```python
from pydantic import BaseModel
from fastapi_ronin.cache import cache
from fastapi_ronin.decorators import action


class StatsSchema(BaseModel):
    total: int
    called_cache: int = 0


@action(methods=['GET'], detail=False)
async def stats(self) -> StatsSchema:
    called = (await cache.get('stats:call') or 0) + 1
    await cache.set('stats:call', called, ttl=60)
    return StatsSchema(total=await Company.all().count(), called_cache=called)
```

## Testing Notes

Use in-memory cache in tests:

```python
await cache.init(None, namespace='test')
await cache.clear()
```

Close the client after each test session when possible:

```python
await cache.close()
```

The global cache client ignores repeated `init()` calls while initialized. If a
test needs a different backend or namespace, call `close()` first.
