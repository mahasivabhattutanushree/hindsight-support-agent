# AI Customer Support Agent with Persistent Memory

An AI-powered customer support agent that remembers each customer across sessions using [Hindsight](https://github.com/vectorize-io/hindsight), a memory system by Vectorize. Unlike typical support bots that forget everything between conversations, this agent recalls a customer's full history automatically — no repeated explanations needed.

## The Problem

Most AI support bots are stateless. Every conversation starts from zero, forcing customers to repeat their issue every single time they reach out. This is frustrating for customers and wastes time for support teams.

## The Solution

This agent uses Hindsight to give every customer a persistent memory bank:

- **Recall** — before responding, the agent queries Hindsight for relevant past context about that specific customer.
- **Retain** — after every exchange, the agent saves the conversation back to Hindsight, so future sessions (even days later) start with full context.

Each customer gets an isolated memory bank (`customer-<id>`), so information never leaks between different customers.

The agent is also instructed to only state facts that actually exist in memory — it will not invent delivery dates, tracking links, or promises it can't keep. If a detail isn't in memory, it says so honestly instead of guessing.

## Two Ways to Try It

**1. Chat UI (`app.py`)** — a side-by-side Streamlit interface showing a memoryless agent and a Hindsight-powered agent answering the same message live, with a sidebar showing exactly what Hindsight recalled.

```bash
pip install hindsight-client groq streamlit
python -m streamlit run app.py
```

**2. Terminal demo (`support_agent.py`)** — a scripted walkthrough covering all three demo parts below in plain text output.

```bash
pip install hindsight-client groq
python support_agent.py
```

Set your API keys as environment variables (`HINDSIGHT_API_KEY`, `GROQ_API_KEY`), or for the Streamlit app, in a `.streamlit/secrets.toml` file (not committed to this repo).

## Demo

1. **Without memory** — a baseline agent that has no idea what a customer means when they refer to a past issue.
2. **With Hindsight memory** — the same agent, now recalling and using real history from a previous session, including stated preferences (e.g. "contact me by email") and evolving issues.
3. **Memory isolation** — a second customer's agent has zero knowledge of the first customer's issue, proving memories stay separate per customer.

## Tech Stack

- [Hindsight](https://hindsight.vectorize.io/) — persistent agent memory (retain/recall)
- [Groq](https://groq.com/) — LLM inference (`openai/gpt-oss-120b`)
- [Streamlit](https://streamlit.io/) — chat interface
- Python 3

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
