"""
Support agent with persistent memory (Hindsight + Groq) - split-screen demo.

Left panel : the same agent with NO long-term memory.
Right panel: the agent with Hindsight memory (recall before reply, retain after).
Type one message, watch both answer. Click "Start new session" to wipe the
chat windows (not the memory) and see who still remembers the customer.

Run:  python -m streamlit run app.py
Keys: set GROQ_API_KEY and HINDSIGHT_API_KEY as environment variables,
      or in .streamlit/secrets.toml (local) / App settings > Secrets (cloud).
"""

import os
import streamlit as st
from groq import Groq
from hindsight_client import Hindsight
from hindsight_client_api.exceptions import NotFoundException

GROQ_MODEL = "openai/gpt-oss-120b"

st.set_page_config(page_title="Support agent with memory", layout="wide")


def get_key(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        try:
            value = st.secrets[name]
        except Exception:
            value = None
    if not value:
        st.error(f"Missing {name}. Set it as an environment variable or in Streamlit secrets.")
        st.stop()
    return value


@st.cache_resource
def get_clients():
    hs = Hindsight(base_url="https://api.hindsight.vectorize.io", api_key=get_key("HINDSIGHT_API_KEY"))
    gq = Groq(api_key=get_key("GROQ_API_KEY"))
    return hs, gq


hindsight, groq = get_clients()

# ---------------------------------------------------------------- demo data
CUSTOMERS = {
    "priya": {
        "name": "Priya Sharma",
        "blurb": "Laptop charger replacement, prefers email",
        "history": [
            "Priya Sharma contacted support on 12 Sep about order ORD-48213: a Dell 65W laptop charger that stopped working after 3 weeks.",
            "Support approved a replacement for ORD-48213 on 14 Sep. It ships via Delhivery, tracking DL7781203. Priya said she prefers updates by email, not phone calls.",
            "On 19 Sep Priya wrote that the replacement had not arrived yet and asked for a firm delivery date. She was polite but getting impatient.",
        ],
        "starter": "Hi, any update on my charger?",
    },
    "rahul": {
        "name": "Rahul Verma",
        "blurb": "Missing headphones order, frustrated",
        "history": [
            "Rahul Verma reported on 8 Sep that order ORD-51877 (boAt Rockerz 450 headphones) never arrived, 9 days after the promised date.",
            "Courier BlueDart marked ORD-51877 as delivered on 10 Sep, but Rahul said nobody came. Support opened a trace with BlueDart (case BD-99214).",
            "Rahul said he wants a refund, not a replacement, if the trace fails. He was frustrated about repeating himself.",
        ],
        "starter": "Any update on my order?",
    },
    "ananya": {
        "name": "Ananya Iyer",
        "blurb": "Brand new customer, no history",
        "history": [],
        "starter": "Hi, my app keeps crashing when I open it.",
    },
}

# ---------------------------------------------------------------- helpers
def bank_id(cid: str) -> str:
    return f"customer-{cid}-v1"


def ask_groq(system_prompt: str, history: list[dict]) -> str:
    resp = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system_prompt}] + history,
    )
    return resp.choices[0].message.content


def reply_no_memory(history: list[dict]) -> str:
    system = (
        "You are a customer support agent for an online electronics store. "
        "You only know what is said in this conversation. You have no records of "
        "earlier conversations. Keep replies under 80 words."
    )
    return ask_groq(system, history)


def recall(cid: str, query: str) -> list[str]:
    try:
        result = hindsight.recall(bank_id=bank_id(cid), query=query)
        return [m.text for m in result.results] if result.results else []
    except NotFoundException:
        return []


def reply_with_memory(cid: str, history: list[dict], query: str) -> tuple[str, list[str]]:
    memories = recall(cid, query)
    context = "\n".join(f"- {m}" for m in memories) if memories else "No prior history."
    system = (
        "You are a customer support agent for an online electronics store.\n"
        f"Long-term memory about this customer (from Hindsight):\n{context}\n\n"
        "STRICT RULE: You may only state a specific date, time, tracking link, price, or claim "
        "that an email/call was already sent IF that exact detail is written word-for-word in "
        "the memory above. The memory above does NOT contain any delivery date, does NOT contain "
        "a tracking link, and does NOT say any email was sent. Therefore you must NOT mention a "
        "delivery date, a tracking link, or say an email was sent, under any circumstances. "
        "Instead say something like 'I don't have an exact delivery date yet, let me check and "
        "follow up.' You may mention the order number, item, and courier name only if they "
        "appear above. Do not promise to send emails or make calls. "
        "Keep replies under 80 words."
    )
    reply = ask_groq(system, history)
    hindsight.retain(
        bank_id=bank_id(cid),
        content=f"Customer said: {query}\nAgent replied: {reply}",
    )
    return reply, memories


def seed_history(cid: str) -> int:
    items = CUSTOMERS[cid]["history"]
    for text in items:
        hindsight.retain(bank_id=bank_id(cid), content=text)
    return len(items)


# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("chats", {})       # {cid: {"plain": [...], "mem": [...]}}
ss.setdefault("recalled", [])    # memories used for the last reply
ss.setdefault("session_no", 1)


def chat_for(cid: str) -> dict:
    return ss.chats.setdefault(cid, {"plain": [], "mem": []})


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Customer")
    cid = st.selectbox(
        "Who is contacting support?",
        list(CUSTOMERS),
        format_func=lambda k: f"{CUSTOMERS[k]['name']} - {CUSTOMERS[k]['blurb']}",
    )
    cust = CUSTOMERS[cid]

    if cust["history"]:
        if st.button("Load past support history", use_container_width=True):
            with st.spinner("Saving past sessions to Hindsight..."):
                n = seed_history(cid)
            st.success(f"Saved {n} past interactions to this customer's memory bank.")
        st.caption("Writes 3 earlier tickets into Hindsight so the agent has a history to recall. Click once per customer.")

    if st.button("Start new session", use_container_width=True):
        ss.chats[cid] = {"plain": [], "mem": []}
        ss.recalled = []
        ss.session_no += 1
        st.rerun()
    st.caption("Clears both chat windows. Hindsight memory stays.")

    st.divider()
    st.subheader("What Hindsight recalled")
    if ss.recalled:
        for m in ss.recalled:
            st.info(m)
    else:
        st.caption("Nothing recalled yet. Send a message.")

# ---------------------------------------------------------------- main
st.title("Support agent that remembers")
st.write(
    f"Session {ss.session_no} with **{cust['name']}**. "
    "Both agents get the same message. Only the right one has long-term memory."
)

chats = chat_for(cid)
prompt = st.chat_input(f"Message as {cust['name']}, e.g. \"{cust['starter']}\"")

if prompt:
    chats["plain"].append({"role": "user", "content": prompt})
    chats["mem"].append({"role": "user", "content": prompt})
    with st.spinner("Both agents are replying..."):
        try:
            plain = reply_no_memory(chats["plain"])
            mem, recalled = reply_with_memory(cid, chats["mem"], prompt)
        except Exception as e:  # keep the demo alive on API errors
            st.error(f"Request failed: {e}")
            chats["plain"].pop()
            chats["mem"].pop()
            st.stop()
    chats["plain"].append({"role": "assistant", "content": plain})
    chats["mem"].append({"role": "assistant", "content": mem})
    ss.recalled = recalled
    st.rerun()

left, right = st.columns(2, gap="large")
for col, key, title, note in (
    (left, "plain", "Without memory", "Knows only this conversation"),
    (right, "mem", "With Hindsight memory", "Recalls past sessions, saves each exchange"),
):
    with col:
        st.subheader(title)
        st.caption(note)
        box = st.container(height=460, border=True)
        with box:
            if not chats[key]:
                st.caption("Send a message below to start.")
            for msg in chats[key]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])