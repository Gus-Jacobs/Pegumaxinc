# Python AI Engineering: APIs & Implementation

*A hands-on course for engineers who want to wire real Python applications into modern AI architectures. Move past notebook demos and build production-grade integrations, agents, and orchestrated pipelines.*

---

## Module 1: The AI Engineering Landscape
**Orient yourself in the modern LLM stack so you know which layer you're building at and why.**

- The engineer's view of LLMs: tokens, context windows, and inference as an API call
- Mapping the stack: model providers, SDKs, orchestration frameworks, and your app
- Setting up a Python project for AI work: environments, dependency management, and secrets handling

---

## Module 2: Calling LLM APIs from Python
**Make your first reliable model calls so you understand the request/response contract every provider shares.**

- Anatomy of a chat completion request: messages, roles, system prompts, and parameters
- Synchronous vs. streaming responses and handling them cleanly in Python
- Sampling controls: temperature, max tokens, stop sequences, and their practical effects

---

## Module 3: Integrating the OpenAI & Anthropic SDKs
**Work fluently with the two leading SDKs so you can build provider-flexible applications.**

- Installing and authenticating the OpenAI and Anthropic Python SDKs
- Comparing the message formats and conventions across providers
- Abstracting a provider-agnostic client layer so you can swap or fall back between models

---

## Module 4: Prompt Engineering in Code
**Treat prompts as engineered, versioned components rather than throwaway strings.**

- Prompt templates, variable injection, and managing prompts as code artifacts
- Few-shot examples, system-prompt design, and role separation for reliability
- Evaluating and iterating on prompts with repeatable test cases

---

## Module 5: Structured JSON Data Extraction
**Force models to return clean, typed data so their output plugs directly into the rest of your system.**

- Structured-output and JSON modes for guaranteed machine-parseable responses
- Defining schemas with Pydantic and validating model output against them
- Robust parsing: handling malformed output, retries, and repair strategies

---

## Module 6: Tool Use & Function Calling
**Give models the ability to call your code so they can act, not just talk.**

- Defining tools/functions and exposing them to the model with schemas
- The tool-call loop: model requests a call, you execute it, you return the result
- Designing safe, well-described tools and validating their arguments

---

## Module 7: Building Local Agent Loops
**Construct an agent from scratch so you understand the reasoning loop before reaching for a framework.**

- The core agent cycle: observe → reason → act → observe, implemented in plain Python
- Managing conversation state, memory, and the context window across turns
- Stopping conditions, step limits, and guardrails to prevent runaway loops

---

## Module 8: Orchestration with LangChain
**Use a framework to compose complex AI workflows so you're not rebuilding plumbing every time.**

- LangChain core concepts: chains, prompts, models, and the expression language
- Building multi-step pipelines and integrating tools and agents
- When a framework helps vs. when raw SDK calls are the better engineering choice

---

## Module 9: Retrieval-Augmented Generation (RAG)
**Ground models in your own data so responses are accurate, current, and source-backed.**

- Embeddings, chunking strategies, and vector databases for semantic search
- Building the retrieval pipeline: index, query, rank, and inject context
- Citing sources and reducing hallucination through grounded prompting

---

## Module 10: Production AI Engineering
**Ship AI features that are reliable, observable, and affordable under real-world usage.**

- Error handling, rate limits, retries with backoff, and timeout strategies
- Cost and latency control: caching, token budgeting, and model routing
- Observability and evaluation: logging, tracing calls, and monitoring output quality in production

---
