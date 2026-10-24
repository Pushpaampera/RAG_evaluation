from collections import defaultdict
from threading import Lock


MAX_HISTORY_MESSAGES = 10

_conversations = defaultdict(list)
_memory_lock = Lock()


def add_message(conversation_id: str, role: str, content: str) -> None:
    if not conversation_id or not conversation_id.strip():
        raise ValueError("Conversation ID is required.")

    if role not in {"user", "assistant"}:
        raise ValueError("Role must be 'user' or 'assistant'.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Message content cannot be empty.")

    with _memory_lock:
        history = _conversations[conversation_id]
        history.append({"role": role, "content": content.strip()})
        _conversations[conversation_id] = history[-MAX_HISTORY_MESSAGES:]


def get_history(conversation_id: str) -> list[dict]:
    if not conversation_id or not conversation_id.strip():
        raise ValueError("Conversation ID is required.")

    with _memory_lock:
        return [message.copy() for message in _conversations[conversation_id]]


def clear_history(conversation_id: str) -> None:
    if not conversation_id or not conversation_id.strip():
        raise ValueError("Conversation ID is required.")

    with _memory_lock:
        _conversations.pop(conversation_id, None)