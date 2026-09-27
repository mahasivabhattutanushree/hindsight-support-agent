"""
AI Customer Support Agent with Persistent Memory (Hindsight + Groq)
--------------------------------------------------------------------
Demonstrates:
1. A support agent WITHOUT memory (forgets everything between messages)
2. The same agent WITH Hindsight memory (remembers customers across sessions)
3. Two different customers to prove memories stay separate per person
"""

import os
from hindsight_client import Hindsight
from hindsight_client_api.exceptions import NotFoundException
from groq import Groq

HINDSIGHT_API_KEY = os.environ.get("HINDSIGHT_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "openai/gpt-oss-120b"

hindsight = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=HINDSIGHT_API_KEY,
)

groq = Groq(api_key=GROQ_API_KEY)


def ask_groq(system_prompt: str, user_message: str) -> str:
    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def chat_no_memory(user_message: str) -> str:
    """A normal support bot with NO memory — every message is a blank slate."""
    system_prompt = "You are a helpful customer support agent. You have no memory of past conversations with this customer."
    return ask_groq(system_prompt, user_message)


def chat_with_memory(customer_id: str, user_message: str) -> str:
    """Support agent that recalls and retains memory per customer using Hindsight."""
    bank_id = f"customer-{customer_id}"

    try:
        recalled = hindsight.recall(bank_id=bank_id, query=user_message)
        memory_context = "\n".join(m.text for m in recalled.results) if recalled.results else "No prior history."
    except NotFoundException:
        memory_context = "No prior history."

    system_prompt = f"""You are a helpful customer support agent.
Here is what you remember about this customer from past interactions:
{memory_context}

Use this history naturally in your reply. If there is relevant past context,
reference it briefly (e.g. "I see you had an issue with X last time").
If there's no history, respond like it's a first-time interaction."""

    reply = ask_groq(system_prompt, user_message)

    hindsight.retain(
        bank_id=bank_id,
        content=f"Customer said: {user_message}\nAgent replied: {reply}",
    )

    return reply


def divider(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


if __name__ == "__main__":
    # ---------- PART 1: THE PROBLEM (no memory) ----------
    divider("PART 1: A support bot WITHOUT memory")
    print("\n[Message 1] Priya: Hi, my laptop charger stopped working, can you help?")
    print("Agent:", chat_no_memory("Hi, my laptop charger stopped working, can you help?"))

    print("\n[Message 2] Priya: Hi again, what's the status on my charger issue?")
    print("Agent:", chat_no_memory("Hi again, what's the status on my charger issue?"))
    print("\n^ Notice the agent has NO idea what 'the charger issue' even refers to. This is the norm for most support bots.")

    # ---------- PART 2: THE FIX (with Hindsight memory) ----------
    divider("PART 2: The SAME agent, now WITH Hindsight memory")
    print("\n[Session 1] Priya: Hi, my laptop charger stopped working, can you help?")
    print("Agent:", chat_with_memory("priya_demo", "Hi, my laptop charger stopped working, can you help?"))

    print("\n[Session 2, later] Priya: Hi again, what's the status on my charger issue?")
    print("Agent:", chat_with_memory("priya_demo", "Hi again, what's the status on my charger issue?"))
    print("\n^ This time the agent remembers, because Hindsight recalled Priya's history automatically.")

    # ---------- PART 3: MEMORY ISOLATION (two customers) ----------
    divider("PART 3: A second customer — proving memories don't mix")
    print("\n[Session 1] Rahul: Hey, I never received my order, it's been a week.")
    print("Agent:", chat_with_memory("rahul_demo", "Hey, I never received my order, it's been a week."))

    print("\n[Session 2, later] Rahul: Any update on my order?")
    print("Agent:", chat_with_memory("rahul_demo", "Any update on my order?"))
    print("\n^ Rahul's agent remembers HIS order issue only — not Priya's charger problem. Each customer has an isolated memory bank.")