"""Shared constants for the interaction-agent package."""

# Keys for the stream writer dict passed between graph.py (producer) and agent.py (consumer).
# Both files must use the same key strings — define them once here.
ADVISOR_KEY_CHUNK = "advisor_chunk"
ADVISOR_KEY_SEARCH_STATUS = "advisor_search_status"

# Keys for training-agent stream events
TRAINING_AGENT_KEY_CHUNK = "training_agent_chunk"
TRAINING_AGENT_KEY_STATUS = "training_agent_status"
TRAINING_AGENT_KEY_JOB_STARTED = "training_agent_job_started"

# Protocol keys for the soofi event envelope emitted by the advisor service.
# Must match the constants defined in advisor/src/a2a_handler.py.
SOOFI_EVENT_KEY = "__soofi_event"
SOOFI_EVENT_SEARCH_STATUS = "search_status"
SOOFI_EVENT_JOB_STARTED = "job_started"
