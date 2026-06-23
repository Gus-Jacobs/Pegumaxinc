# Local AI & Automation Engines

*A build-it-yourself course for engineering self-hosted agent networks that run entirely on your own hardware—no cloud API subscriptions, no per-token fees, full control of your data.*

---

## Module 1: The Self-Hosted Stack & Cost Model
**Understand the full local-first architecture so you can replace expensive cloud APIs with hardware you already own.**

- The economics: cloud per-token costs vs. one-time local hardware investment
- Hardware reality check: RAM, VRAM, and CPU/GPU requirements for usable local models
- Architecture overview: inference engine, automation layer, storage, and how the pieces connect

---

## Module 2: Ollama Setup & Model Serving
**Get a local LLM running and exposed as an API so the rest of your stack can call it like any cloud endpoint.**

- Installing Ollama and pulling, running, and managing models from the command line
- The local REST API: chat/generate endpoints and pointing tools at `localhost`
- Custom `Modelfile` configuration for system prompts, parameters, and named model variants

---

## Module 3: Model Quantization & Selection
**Pick and shrink models so they run fast on your hardware without sacrificing the quality your tasks need.**

- Quantization explained: what Q4, Q5, Q8, and GGUF formats trade off in size vs. accuracy
- Matching model size and quant level to available VRAM/RAM and latency targets
- Benchmarking candidates on your own tasks to find the smallest model that's "good enough"

---

## Module 4: Containerization with Docker
**Run every service in isolated, reproducible containers so your stack is portable, clean, and easy to rebuild.**

- Docker fundamentals: images, containers, volumes, and networks for self-hosters
- Writing `docker-compose` files to define a multi-service stack as code
- Persistent volumes, port mapping, and inter-container networking for service-to-service calls

---

## Module 5: Running n8n in a Local Container
**Stand up a self-hosted automation engine that orchestrates your agents visually and runs 24/7 on your machine.**

- Deploying n8n via Docker Compose with persistent storage and environment config
- The n8n model: nodes, triggers, and connecting workflows to your local Ollama endpoint
- Securing the local instance: credentials store, basic auth, and webhook configuration

---

## Module 6: Building Your First Local Agent Workflow
**Wire an LLM into an automated workflow that takes input, reasons, and produces a useful action end to end.**

- Trigger → prompt → LLM call → parse → act: the anatomy of an agent workflow in n8n
- Structuring prompts and parsing model output into reliable, machine-usable JSON
- Adding tools: HTTP requests, file operations, and shell/code nodes the agent can invoke

---

## Module 7: File-Based State Loops
**Give your agents persistent memory and control flow using the filesystem—no database required.**

- Reading and writing JSON/Markdown state files to persist context between runs
- Designing loop logic: watch a file or folder, process, update state, repeat
- Queues and checkpoints on disk so long-running jobs survive restarts and resume cleanly

---

## Module 8: Multi-Agent Networks & Orchestration
**Coordinate several specialized agents so they hand off work and solve tasks no single agent could.**

- Specialized roles: planner, worker, and reviewer agents passing messages between workflows
- Orchestration patterns: sequential pipelines, fan-out/fan-in, and supervisor loops
- Inter-agent communication via shared files, webhooks, and n8n sub-workflows

---

## Module 9: Local RAG & Knowledge Retrieval
**Ground your agents in your own documents so they answer from your data instead of hallucinating.**

- Local embeddings with Ollama and chunking strategies for your document set
- Self-hosted vector storage and similarity search wired into your workflows
- Building a retrieval step that injects relevant context into prompts at run time

---

## Module 10: Hardening, Scheduling & Reliability
**Turn your prototype into a dependable always-on system that recovers from failures on its own.**

- Scheduling, retries, and error-handling branches so workflows fail gracefully
- Logging, monitoring, and alerting for a headless self-hosted stack
- Backups, container restart policies, and resource limits for stable long-term operation

---
