"""
AI Customer Support Agent with Persistent Memory (Hindsight + Groq)
--------------------------------------------------------------------
Demonstrates:
1. A support agent WITHOUT memory (forgets everything between messages)
2. The SAME agent WITH Hindsight memory, across THREE sessions
3. A second customer, proving memories stay isolated per person

The agent is instructed to only state facts that actually exist in
memory - it will not invent delivery dates, tracking links, or
promises it can't keep.
"""

import os
from hindsight_client import Hindsight
from hindsight_client_api.exceptions import NotFoundException
from groq import Groq

HINDSIGHT_API_KEY = os.environ.get("HINDSIGHT_API_KEY", "PASTE_YOUR_HINDSIGHT_KEY_HERE")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "PASTE_YOUR_GROQ_KEY_HERE")
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
    """A normal support bot with NO memory - every message is a blank slate."""
    system_prompt = (
        "You are a helpful customer support agent for TechNest, an electronics retailer. "
        "You have no memory of past conversations with this customer."
    )
    return ask_groq(system_prompt, user_message)


def chat_with_memory(customer_id: str, user_message: str) -> str:
    """Support agent that recalls and retains memory per customer using Hindsight."""
    bank_id = f"customer-{customer_id}"

    try:
        recalled = hindsight.recall(bank_id=bank_id, query=user_message)
        memory_context = "\n".join(m.text for m in recalled.results) if recalled.results else "No prior history."
    except NotFoundException:
        memory_context = "No prior history."

    system_prompt = f"""You are a helpful customer support agent for TechNest, an electronics retailer.
Here is what you remember about this customer from past interactions:
{memory_context}

STRICT RULE: You may only state a specific date, tracking link, price, or claim that an
email/call was already sent IF that exact detail appears word-for-word in the memory above.
If a detail (like a delivery date) is not in the memory, do NOT invent one - instead say
you don't have that yet and will check and follow up.

Use the memory naturally: mention order numbers and preferences when relevant, and never
make the customer repeat themselves. If there's no history, respond like it's a first-time
interaction."""

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
    print("\n[Message 1] Priya: Hi, my order ORD-48213 charger stopped working, can you help?")
    print("Agent:", chat_no_memory("Hi, my order ORD-48213 charger stopped working, can you help?"))

    print("\n[Message 2] Priya: Hi again, what's the status on my charger issue?")
    print("Agent:", chat_no_memory("Hi again, what's the status on my charger issue?"))
    print("\n^ The agent has NO idea what 'the charger issue' or order ORD-48213 refers to.")

    # ---------- PART 2: MEMORY ACROSS THREE SESSIONS ----------
    divider("PART 2: The SAME agent, now WITH Hindsight memory (3 sessions)")

    print("\n[Session 1] Priya: Hi, my Dell 65W charger (order ORD-48213) stopped working. I'd prefer updates over email, not chat.")
    print("Agent:", chat_with_memory("priya_demo", "Hi, my Dell 65W charger (order ORD-48213) stopped working. I'd prefer updates over email, not chat."))

    print("\n[Session 2] Priya: Hi again, what's the status on my charger issue?")
    print("Agent:", chat_with_memory("priya_demo", "Hi again, what's the status on my charger issue?"))
    print("\n^ The agent recalls the order number and email preference, but does NOT invent a delivery date.")

    print("\n[Session 3] Priya: Update - the replacement arrived but now my laptop won't turn on at all.")
    print("Agent:", chat_with_memory("priya_demo", "Update - the replacement arrived but now my laptop won't turn on at all."))
    print("\n^ The issue has EVOLVED - the agent should connect this to the original charger case.")

    # ---------- PART 3: MEMORY ISOLATION (two customers) ----------
    divider("PART 3: A second customer - proving memories don't mix")
    print("\n[Session 1] Rahul: Hey, my order ORD-51877 (headphones) never arrived, it's been a week.")
    print("Agent:", chat_with_memory("rahul_demo", "Hey, my order ORD-51877 (headphones) never arrived, it's been a week."))

    print("\n[Session 2] Rahul: Any update on my order?")
    print("Agent:", chat_with_memory("rahul_demo", "Any update on my order?"))
    print("\n^ Rahul's agent remembers HIS order ORD-51877 only - not Priya's charger case or her email preference.")
