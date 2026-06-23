# Production Backends with Django & Docker

*An architect's course on building real, scalable web backends—from clean Django design patterns to fully containerized services ready to ship. Build it right, package it cleanly, and deploy with confidence.*

---

## Module 1: Project Architecture & Setup
**Lay down a Django project structure that scales cleanly from prototype to production without painful rewrites.**

- Project vs. app boundaries: splitting a codebase into focused, reusable apps
- Settings architecture: per-environment configs, `.env` files, and the twelve-factor approach
- Virtual environments, dependency pinning, and a sane initial repository layout

---

## Module 2: Django's MVT Design Pattern
**Master Django's take on MVC so your models, views, and templates stay decoupled and maintainable.**

- Models, Views, Templates (MVT) explained and how it maps to classic MVC
- The request/response lifecycle: URL routing, middleware, and view dispatch
- Fat models, thin views, and where business logic actually belongs

---

## Module 3: Data Modeling & the ORM
**Design a relational schema and query it efficiently so your data layer never becomes the bottleneck.**

- Models, relationships, and migrations as version-controlled schema changes
- Querying with the ORM: filtering, related lookups, and aggregation
- Performance: `select_related`/`prefetch_related`, indexing, and avoiding N+1 queries

---

## Module 4: Authentication & Authorization
**Control identity and access so your backend exposes the right data only to the right users.**

- Django's auth system, custom user models, and password handling
- Permissions, groups, and object-level access control
- Token and session strategies for securing API access

---

## Module 5: Building REST APIs
**Construct clean, versioned APIs with Django REST Framework that frontends and partners can consume reliably.**

- Serializers, viewsets, and routers for fast, consistent endpoint construction
- Request validation, pagination, filtering, and API versioning
- Browsable API, throttling, and auto-generated OpenAPI documentation

---

## Module 6: Webhook Integration with Stripe
**Handle inbound webhooks correctly so external events like payments update your system reliably and securely.**

- Webhook fundamentals: receiving, verifying signatures, and returning fast 2xx responses
- Integrating Stripe events (checkout, subscriptions) and reconciling them with your models
- Idempotency, retries, and replay protection so duplicate events never corrupt state

---

## Module 7: Asynchronous Tasks & Background Jobs
**Offload slow work to background workers so your API stays fast under real load.**

- Why blocking work belongs out of the request cycle (emails, webhooks, reports)
- Celery with a Redis/RabbitMQ broker for queued and scheduled tasks
- Retries, task monitoring, and handling failures gracefully

---

## Module 8: Containerizing with Docker
**Package your backend and its dependencies into reproducible images that run identically everywhere.**

- Writing an efficient `Dockerfile`: multi-stage builds, layer caching, and slim images
- Environment configuration, secrets, and keeping images stateless
- `.dockerignore`, non-root users, and image-hardening best practices

---

## Module 9: Multi-Service Orchestration with Compose
**Wire Django, your database, cache, and workers into one cohesive stack that spins up with a single command.**

- `docker-compose` for orchestrating web, database, Redis, and Celery services
- Service networking, persistent volumes, and health checks between containers
- Running migrations, collecting static files, and seeding data in a containerized workflow

---

## Module 10: Production Deployment & Scaling
**Ship your containerized backend to production with the serving, scaling, and observability a real system needs.**

- Production serving: Gunicorn/ASGI behind Nginx, static/media handling, and TLS
- Horizontal scaling, load balancing, and zero-downtime deployment basics
- Logging, monitoring, and health checks for a backend you can actually operate

---
