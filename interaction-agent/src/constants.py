"""Shared constants for the interaction-agent package."""

# Keys for the stream writer dict passed between graph.py (producer) and agent.py (consumer).
# Both files must use the same key strings — define them once here.
ADVISOR_KEY_CHUNK = "advisor_chunk"
ADVISOR_KEY_SEARCH_STATUS = "advisor_search_status"

# Protocol keys for the soofi event envelope emitted by the advisor service.
# Must match the constants defined in advisor/src/a2a_handler.py.
SOOFI_EVENT_KEY = "__soofi_event"
SOOFI_EVENT_SEARCH_STATUS = "search_status"
