"""Shared constants for the interaction-agent package."""

# Keys for custom event data passed between graph.py (producer) and sse_stream.py (consumer).
# Both files must use the same key strings — define them once here.
ADVISOR_KEY_CHUNK = "advisor_chunk"
ADVISOR_KEY_SEARCH_STATUS = "advisor_search_status"

# Keys for training-agent stream events
TRAINING_AGENT_KEY_CHUNK = "training_agent_chunk"
TRAINING_AGENT_KEY_STATUS = "training_agent_status"
TRAINING_AGENT_KEY_JOB_STARTED = "training_agent_job_started"

# Keys for doc viewer control events
DOC_VIEWER_KEY = "doc_viewer"
CONTROL_DOC_VIEWER_TOOL = "control_doc_viewer"

# Custom event names for adispatch_custom_event (must match graph.py → sse_stream.py)
ADVISOR_EVENT = "advisor_event"
TRAINING_EVENT = "training_event"

# Keys for agent card viewer events
AGENT_CARD_KEY = "agent_card"
AGENT_CARD_EVENT = "agent_card_event"

# Keys for training view control events
TRAINING_VIEW_KEY = "training_view"
TRAINING_VIEW_EVENT = "training_view_event"

# Protocol keys for the soofi event envelope emitted by the advisor service.
# Must match the constants defined in advisor/src/a2a_handler.py.
SOOFI_EVENT_KEY = "__soofi_event"
SOOFI_EVENT_SEARCH_STATUS = "search_status"
SOOFI_EVENT_JOB_STARTED = "job_started"
