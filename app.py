from datetime import datetime
import json
from pathlib import Path
import time
from uuid import uuid4

import requests
import streamlit as st


API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
PLACEHOLDER_TOKEN = "paste_your_hugging_face_token_here"
DEFAULT_CHAT_TITLE = "New Chat"
CHATS_DIR = Path("chats")
MEMORY_FILE = Path("memory.json")
STREAM_DELAY_SECONDS = 0.02
MEMORY_LIST_KEYS = {"interests", "favorite_topics"}
MEMORY_SCALAR_KEYS = {"name", "preferred_language", "communication_style"}


def get_hf_token() -> str | None:
    try:
        token = st.secrets["HF_TOKEN"].strip()
    except Exception:
        token = ""

    if not token or token == PLACEHOLDER_TOKEN:
        st.error(
            "Missing Hugging Face token. Add `HF_TOKEN` to `.streamlit/secrets.toml` "
            "with your real token before running the app."
        )
        return None
    return token


def parse_json_object(text: str) -> dict:
    stripped = text.strip()
    if not stripped:
        return {}

    try:
        data = json.loads(stripped)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        data = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def load_memory() -> dict:
    if not MEMORY_FILE.exists():
        return {}

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        st.warning("Memory file was invalid, so memory was reset for this session.")
        return {}

    return data if isinstance(data, dict) else {}


def save_memory(memory: dict) -> None:
    MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def clear_memory() -> None:
    st.session_state.memory = {}
    save_memory(st.session_state.memory)


def merge_memory(existing_memory: dict, new_memory: dict) -> dict:
    merged = dict(existing_memory)

    for key in MEMORY_SCALAR_KEYS:
        value = new_memory.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()

    for key in MEMORY_LIST_KEYS:
        existing_values = merged.get(key, [])
        if not isinstance(existing_values, list):
            existing_values = []

        new_values = new_memory.get(key, [])
        if isinstance(new_values, str):
            new_values = [new_values]
        if not isinstance(new_values, list):
            continue

        combined = []
        for item in [*existing_values, *new_values]:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned and cleaned not in combined:
                    combined.append(cleaned)

        if combined:
            merged[key] = combined

    for key, value in new_memory.items():
        if key in MEMORY_SCALAR_KEYS or key in MEMORY_LIST_KEYS:
            continue
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()

    return merged


def build_memory_system_prompt(memory: dict) -> str | None:
    if not memory:
        return None

    return (
        "You are a helpful assistant. Use the following stored user memory to "
        "personalize responses when relevant, but do not mention this memory unless "
        "it naturally helps the conversation.\n\n"
        f"User memory:\n{json.dumps(memory, indent=2)}"
    )


def build_api_messages(messages: list[dict]) -> list[dict]:
    memory_prompt = build_memory_system_prompt(st.session_state.memory)
    if memory_prompt is None:
        return messages
    return [{"role": "system", "content": memory_prompt}, *messages]


def extract_user_memory(user_message: str) -> dict:
    token = get_hf_token()
    if token is None:
        return {}

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract personal traits or preferences from the user's message. "
                    "Return only a JSON object. Use keys like name, preferred_language, "
                    "interests, favorite_topics, and communication_style when relevant. "
                    "If nothing useful is present, return {}."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 200,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException:
        return {}

    if not response.ok:
        return {}

    try:
        data = response.json()
    except ValueError:
        return {}

    choices = data.get("choices")
    if not choices:
        return {}

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    if not isinstance(content, str):
        return {}

    return parse_json_object(content)


def stream_chat_completion(
    messages: list[dict], stream_state: dict, max_tokens: int = 512
):
    token = get_hf_token()
    if token is None:
        stream_state["completed"] = False
        return

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": MODEL_NAME,
        "messages": build_api_messages(messages),
        "max_tokens": max_tokens,
        "stream": True,
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30,
            stream=True,
        )
    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")
        stream_state["completed"] = False
        return

    if not response.ok:
        detail = response.text.strip() or "No additional error details were returned."
        st.error(f"API request failed with status {response.status_code}: {detail}")
        stream_state["completed"] = False
        return

    try:
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            if not raw_line.startswith("data:"):
                continue

            data_str = raw_line.removeprefix("data:").strip()
            if not data_str:
                continue

            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                st.error("The API returned a streaming chunk that was not valid JSON.")
                stream_state["completed"] = False
                return

            choices = data.get("choices")
            if not choices:
                continue

            delta = choices[0].get("delta", {})
            content = delta.get("content")

            if isinstance(content, str) and content:
                time.sleep(STREAM_DELAY_SECONDS)
                yield content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_value = item.get("text", "")
                        if text_value:
                            time.sleep(STREAM_DELAY_SECONDS)
                            yield text_value
        stream_state["completed"] = True
    except requests.RequestException as exc:
        st.error(f"Streaming failed: {exc}")
        stream_state["completed"] = False
        return
    finally:
        response.close()


def ensure_chats_dir() -> None:
    CHATS_DIR.mkdir(exist_ok=True)


def get_chat_file_path(chat_id: str) -> Path:
    return CHATS_DIR / f"{chat_id}.json"


def save_chat(chat: dict) -> None:
    ensure_chats_dir()
    chat_path = get_chat_file_path(chat["id"])
    chat_path.write_text(json.dumps(chat, indent=2), encoding="utf-8")


def load_chats_from_disk() -> list[dict]:
    ensure_chats_dir()
    chats = []

    for chat_path in sorted(CHATS_DIR.glob("*.json")):
        try:
            chat = json.loads(chat_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            st.warning(f"Skipping invalid chat file: {chat_path.name}")
            continue

        if not all(key in chat for key in ("id", "title", "timestamp", "messages")):
            st.warning(f"Skipping incomplete chat file: {chat_path.name}")
            continue

        if not isinstance(chat["messages"], list):
            st.warning(f"Skipping chat with invalid messages: {chat_path.name}")
            continue

        chats.append(chat)

    chats.sort(key=lambda chat: chat["timestamp"], reverse=True)
    return chats


def delete_chat_file(chat_id: str) -> None:
    chat_path = get_chat_file_path(chat_id)
    if chat_path.exists():
        chat_path.unlink()


def create_chat() -> dict:
    created_at = datetime.now()
    return {
        "id": str(uuid4()),
        "title": DEFAULT_CHAT_TITLE,
        "timestamp": created_at.isoformat(),
        "messages": [],
    }


def get_chat_index(chat_id: str | None) -> int | None:
    if chat_id is None:
        return None

    for index, chat in enumerate(st.session_state.chats):
        if chat["id"] == chat_id:
            return index
    return None


def get_active_chat() -> dict | None:
    chat_index = get_chat_index(st.session_state.active_chat_id)
    if chat_index is None:
        return None
    return st.session_state.chats[chat_index]


def format_timestamp(timestamp: str) -> str:
    return datetime.fromisoformat(timestamp).strftime("%b %d, %I:%M %p")


def set_active_chat(chat_id: str) -> None:
    st.session_state.active_chat_id = chat_id


def add_new_chat() -> None:
    chat = create_chat()
    st.session_state.chats.append(chat)
    st.session_state.active_chat_id = chat["id"]
    save_chat(chat)


def delete_chat(chat_id: str) -> None:
    chat_index = get_chat_index(chat_id)
    if chat_index is None:
        return

    was_active = st.session_state.active_chat_id == chat_id
    st.session_state.chats.pop(chat_index)
    delete_chat_file(chat_id)

    if not was_active:
        return

    if st.session_state.chats:
        fallback_index = min(chat_index, len(st.session_state.chats) - 1)
        st.session_state.active_chat_id = st.session_state.chats[fallback_index]["id"]
    else:
        st.session_state.active_chat_id = None


def update_chat_title(chat: dict, user_prompt: str) -> None:
    if chat["title"] != DEFAULT_CHAT_TITLE:
        return

    trimmed_prompt = user_prompt.strip()
    if not trimmed_prompt:
        return

    chat["title"] = trimmed_prompt[:30] + ("..." if len(trimmed_prompt) > 30 else "")


st.set_page_config(page_title="My AI Chat", layout="wide")

st.title("My AI Chat")
st.write(
    "Chat with the Hugging Face Inference Router using Streamlit's native chat UI."
)

if "chats" not in st.session_state:
    st.session_state.chats = load_chats_from_disk()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = (
        st.session_state.chats[0]["id"] if st.session_state.chats else None
    )

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

with st.sidebar:
    st.header("Chats")

    if st.button("New Chat", use_container_width=True):
        add_new_chat()

    if not st.session_state.chats:
        st.info("No chats yet. Create a new chat to begin.")
    else:
        for chat in st.session_state.chats:
            is_active = chat["id"] == st.session_state.active_chat_id
            row = st.columns([5, 1])

            button_label = f"{chat['title']}\n{format_timestamp(chat['timestamp'])}"
            button_type = "primary" if is_active else "secondary"

            with row[0]:
                if st.button(
                    button_label,
                    key=f"select_{chat['id']}",
                    use_container_width=True,
                    type=button_type,
                ):
                    set_active_chat(chat["id"])

            with row[1]:
                if st.button(
                    "✕",
                    key=f"delete_{chat['id']}",
                    use_container_width=True,
                ):
                    delete_chat(chat["id"])
                    st.rerun()

    with st.expander("User Memory", expanded=True):
        if st.button("Clear Memory", use_container_width=True):
            clear_memory()
            st.rerun()

        if st.session_state.memory:
            st.json(st.session_state.memory)
        else:
            st.caption("No stored user memory yet.")

active_chat = get_active_chat()

if active_chat is None:
    st.info("Create a new chat from the sidebar to start a conversation.")
else:
    for message in active_chat["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Type a message and press Enter")

    if prompt:
        user_message = {"role": "user", "content": prompt}
        active_chat["messages"].append(user_message)
        update_chat_title(active_chat, prompt)
        save_chat(active_chat)

        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            stream_state = {"completed": False}
            reply = st.write_stream(
                stream_chat_completion(active_chat["messages"], stream_state)
            )
            if stream_state["completed"] and isinstance(reply, str) and reply.strip():
                active_chat["messages"].append({"role": "assistant", "content": reply})
                save_chat(active_chat)
                extracted_memory = extract_user_memory(prompt)
                if extracted_memory:
                    st.session_state.memory = merge_memory(
                        st.session_state.memory, extracted_memory
                    )
                    save_memory(st.session_state.memory)
