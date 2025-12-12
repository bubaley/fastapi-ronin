# FastAPI Ronin

<p align="center">
  <img align="center" src="docs/assets/logo.png" alt="logo" width="200"/>
  <h1 align="center">FastAPI Ronin</h1>
</p>
<p align="center" markdown=1>
  <i>Build REST APIs with Django REST Framework patterns in FastAPI</i>
</p>
<p align="center" markdown=1>
<a href="https://pypi.org/project/fastapi-ronin/">
  <img src="https://img.shields.io/pypi/v/fastapi-ronin?color=%2334D058&label=pypi%20package" alt="PyPi Version"/>
</a>
<a href="https://pypi.org/project/fastapi-ronin/">
  <img src="https://img.shields.io/pypi/pyversions/fastapi-ronin.svg?color=%2334D058" alt="Supported Python Versions"/>
</a>
<a href="https://github.com/bubaley/fastapi-ronin/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"/>
</a>
</p>

<hr>

**Transform your FastAPI development with familiar Django REST Framework patterns.**

FastAPI Ronin brings the beloved patterns and conventions from Django REST Framework to FastAPI, providing a structured and efficient way to build REST APIs. With familiar concepts like ViewSets, permissions, pagination, and serialization, you can rapidly develop robust API applications.

Just like skilled ronin who master their craft with precision and expertise, FastAPI Ronin helps you build reliable, well-structured APIs with time-tested patterns and best practices.

<hr>
<p><b>Documentation</b>: <a class="link" href="https://bubaley.github.io/fastapi-ronin">bubaley.github.io/fastapi-ronin</a></p>
<hr>

<div style="margin: 2rem 0;">
  <a href="https://bubaley.github.io/fastapi-ronin/quick-start/" class="get-started-btn">
    Get Started
  </a>
</div>

## 📦 Installation

Install FastAPI Ronin using UV:

```bash
uv add fastapi-ronin
```

## 🚀 Quick Example

Here's a complete example showing how to build a REST API with FastAPI Ronin:

```python
# main.py - Complete FastAPI Ronin application
from datetime import datetime

from fastapi import APIRouter, FastAPI
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import PydanticModel
from tortoise.models import Model

from fastapi_ronin.decorators import action, schema, viewset
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


# Database setup
def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url='sqlite://db.sqlite3',
        modules={'models': ['main']},
        generate_schemas=True,
        add_exception_handlers=True,
    )


# Models
class Company(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


# Schemas
@schema(model=Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str


@schema(model=Company)
class CompanyReadSchema(PydanticModel):
    id: int
    name: str
    full_name: str
    created_at: datetime
    updated_at: datetime


# Views
router = APIRouter(prefix='/companies', tags=['companies'])


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper

    # permission_classes = [IsAuthenticatedOrReadOnly]

    @action(methods=['GET'], detail=False)
    async def stats(self) -> dict[str, int]:
        return {'total': await Company.all().count()}


# Application
app = FastAPI(title='My API')
register_database(app)
app.include_router(router)
```

Start server:

```bash
uvicorn main:app --reload
```

 Try API Endpoints:

```python
"""
This creates the following endpoints:
- GET /companies/ - List companies with pagination
- POST /companies/ - Create new company
- GET /companies/{item_id}/ - Get specific company
- PUT /companies/{item_id}/ - Update company
- DELETE /companies/{item_id}/ - Delete company
- GET /companies/stats/ - Custom stats endpoint

Example API Responses:

GET /companies/ (with pagination wrapper):
{
  "data": [
    {
      "id": 1,
      "name": "Acme Corp",
      "full_name": "Acme Corporation Ltd.",
      "created_at": "2023-01-01T10:00:00Z",
      "updated_at": "2023-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 5,
    "total_items": 47
  }
}

GET /companies/1/ (with single wrapper):
{
  "data": {
    "id": 1,
    "name": "Acme Corp",
    "full_name": "Acme Corporation Ltd.",
    "created_at": "2023-01-01T10:00:00Z",
    "updated_at": "2023-01-01T10:00:00Z"
  }
}

GET /companies/stats/ (custom action):
{
  "total": 123
}
"""
```

## ✨ Key Features

<div class="feature-card">
  <h3>🎯 ViewSets</h3>
Django-like ViewSets with automatic CRUD operations and custom actions. Build complete REST APIs with minimal boilerplate code.
</div>

<div class="feature-card">
<h3>🔒 Permissions</h3>
Built-in permission system with customizable access control. Protect your endpoints with authentication and authorization rules.
</div>

<div class="feature-card">
<h3>📄 Pagination</h3>
Multiple pagination strategies out of the box: Limit/Offset and Page Number. You can easily customize or override pagination classes to suit your needs.
</div>

<div class="feature-card">
<h3>📋 Schema Generation</h3>
Intelligent schema generation with meta classes for fine-grained control over API serialization.
</div>

<div class="feature-card">
<h3>🔄 Response Wrappers</h3>
Consistent API response formatting with customizable wrapper classes.
</div>

<div class="feature-card">
<h3>⚡ State Management</h3>
Request-scoped state management for sharing data across middleware and view components.
</div>

## 🎯 Philosophy

FastAPI Ronin is designed with these principles in mind:

- **Familiar**: If you know Django REST Framework, you already know FastAPI Ronin
- **Flexible**: Customize every aspect while maintaining sensible defaults
- **Fast**: Built on FastAPI's high-performance foundation
- **Modular**: Use only what you need, when you need it

## 📚 Getting Started

Ready to build amazing APIs? Start with our [Quick Start guide](https://bubaley.github.io/fastapi-ronin/quick-start/) to get up and running in minutes.

Want to dive deeper? Explore our comprehensive guides:

- [ViewSets](https://bubaley.github.io/fastapi-ronin/viewsets/) - Learn about the core ViewSet concepts
- [Schemas & Meta](https://bubaley.github.io/fastapi-ronin/schemas/) - Master schema generation and meta classes
- [Permissions](https://bubaley.github.io/fastapi-ronin/permissions/) - Secure your APIs with permission classes
- [Pagination](https://bubaley.github.io/fastapi-ronin/pagination/) - Implement efficient data pagination
- [State Management](https://bubaley.github.io/fastapi-ronin/state/) - Manage request-scoped state
- [Response Wrappers](https://bubaley.github.io/fastapi-ronin/wrappers/) - Format consistent API responses

## 🤝 Community

FastAPI Ronin is open source and welcomes contributions! Whether you're reporting bugs, suggesting features, or submitting pull requests, your involvement helps make the library better for everyone.

- **GitHub**: [github.com/bubaley/fastapi-ronin](https://github.com/bubaley/fastapi-ronin)
- **Issues**: Report bugs and request features
- **Discussions**: Get help and share ideas

## 📄 License

FastAPI Ronin is released under the [MIT License](https://github.com/bubaley/fastapi-ronin/blob/main/LICENSE).
