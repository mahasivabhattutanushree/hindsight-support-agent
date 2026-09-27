# AI Customer Support Agent with Persistent Memory

An AI-powered customer support agent that remembers each customer across sessions using [Hindsight](https://github.com/vectorize-io/hindsight), a memory system by Vectorize. Unlike typical support bots that forget everything between conversations, this agent recalls a customer's full history automatically — no repeated explanations needed.

## The Problem

Most AI support bots are stateless. Every conversation starts from zero, forcing customers to repeat their issue every single time they reach out. This is frustrating for customers and wastes time for support teams.

## The Solution

This agent uses Hindsight to give every customer a persistent memory bank:

- **Recall** — before responding, the agent queries Hindsight for relevant past context about that specific customer.
- **Retain** — after every exchange, the agent saves the conversation back to Hindsight, so future sessions (even days later) start with full context.

Each customer gets an isolated memory bank (`customer-<id>`), so information never leaks between different customers.

## Demo

Running the script shows three things:

1. **Without memory** — a baseline agent that has no idea what a customer means when they refer to a past issue.
2. **With Hindsight memory** — the same agent, now recalling and using real history from a previous session.
3. **Memory isolation** — a second customer's agent has zero knowledge of the first customer's issue, proving memories stay separate per customer.

## Tech Stack

- **[Hindsight](https://hindsight.vectorize.io/)** — persistent agent memory (retain/recall)
- **[Groq](https://groq.com/)** — LLM inference (`openai/gpt-oss-120b`)
- **Python 3**

## Setup

```bash
pip install hindsight-client groq
python support_agent.py
```

Set your API keys as environment variables (`HINDSIGHT_API_KEY`, `GROQ_API_KEY`), or edit them directly at the top of `support_agent.py`.

## How Hindsight Is Used

Every customer interaction is wrapped by two Hindsight calls:

```python
recalled = hindsight.recall(bank_id=bank_id, query=user_message)
```
This pulls relevant memories about the customer before generating a reply.

```python
hindsight.retain(bank_id=bank_id, content=f"Customer said: {user_message}\nAgent replied: {reply}")
```
This saves the exchange so future sessions have full context.

## What's Next

Future versions could expand memory to track sentiment over time, summarize recurring issue patterns across a customer base, and integrate with a real ticketing system.