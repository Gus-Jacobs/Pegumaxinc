# System Design & Scalable Architecture

*A solutions architect's course bridging the gap between writing an app and engineering systems that serve millions. Learn the building blocks, tradeoffs, and patterns behind enterprise-scale infrastructure.*

---

## Module 1: Foundations of Scalable Systems
**Build the vocabulary and mental models that every system design decision is measured against.**

- Scalability, availability, reliability, and latency—what each means and how they trade off
- Vertical vs. horizontal scaling and why "just add a bigger server" eventually fails
- Back-of-the-envelope estimation: capacity, throughput, and identifying bottlenecks

---

## Module 2: Monoliths vs. Microservices
**Choose the right architectural style by understanding what each buys you and what it costs.**

- The monolith's strengths and where it genuinely breaks down at scale
- Microservices: service boundaries, independent deployment, and operational overhead
- Migration reality: the modular monolith and decomposing a system incrementally

---

## Module 3: Load Balancing & Traffic Distribution
**Spread traffic across servers so your system stays fast and available as demand grows.**

- Load balancer types (L4 vs. L7) and algorithms (round-robin, least-connections, hashing)
- Health checks, failover, and removing unhealthy nodes automatically
- Sticky sessions, SSL termination, and where the balancer sits in your topology

---

## Module 4: Caching Strategies with Redis
**Cut latency and database load dramatically by serving hot data from memory the right way.**

- Cache patterns: cache-aside, read-through, write-through, and write-behind
- Redis in practice: data structures, TTLs, and eviction policies
- Cache invalidation, stampede protection, and avoiding stale-data pitfalls

---

## Module 5: Database Scaling & Sharding
**Scale your data layer past a single machine so the database stops being the ceiling.**

- Read replicas, replication lag, and separating read/write paths
- Sharding strategies: range, hash, and directory-based partitioning
- Shard key selection, hotspots, rebalancing, and cross-shard query challenges

---

## Module 6: Asynchronous Processing & Message Queues
**Decouple services with queues so spikes and slow work never take down your request path.**

- Synchronous vs. asynchronous communication and when to choose each
- Message queues and brokers (Kafka, RabbitMQ, SQS) for buffering and decoupling
- Delivery guarantees, idempotency, ordering, and dead-letter handling

---

## Module 7: API Design, Gateways & Rate Limiting
**Expose services through a robust API layer that protects backends and stays fair under load.**

- API gateway responsibilities: routing, auth, aggregation, and observability
- Rate limiting algorithms: token bucket, leaky bucket, and fixed/sliding windows
- Throttling, backpressure, and graceful degradation under overload

---

## Module 8: Data Consistency & Distributed Patterns
**Reason about correctness across many machines so distributed state doesn't betray you.**

- The CAP theorem and choosing consistency vs. availability deliberately
- Strong vs. eventual consistency and what each means for users
- Distributed transactions, the saga pattern, and handling partial failure

---

## Module 9: Resilience, Observability & Fault Tolerance
**Design systems that survive failure and tell you what's happening before users notice.**

- Failure isolation: timeouts, retries with backoff, circuit breakers, and bulkheads
- Observability pillars: metrics, logging, and distributed tracing
- Redundancy, graceful degradation, and avoiding single points of failure

---

## Module 10: Putting It Together—Design Case Studies
**Synthesize every building block by architecting real large-scale systems end to end.**

- A repeatable framework for tackling any system design problem or interview
- End-to-end walkthroughs (e.g., URL shortener, news feed, ride-sharing backend)
- Evaluating tradeoffs, defending decisions, and evolving a design as scale grows

---
