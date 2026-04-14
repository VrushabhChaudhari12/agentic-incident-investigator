import os

# LLM settings
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))

# Agent loop settings
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "8"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.9"))
MIN_TOOLS_BEFORE_ANSWER = int(os.getenv("MIN_TOOLS_BEFORE_ANSWER", "2"))

# AWS / log settings
DEFAULT_LOG_WINDOW_MINUTES = int(os.getenv("DEFAULT_LOG_WINDOW_MINUTES", "30"))
DEFAULT_AWS_REGION = os.getenv("DEFAULT_AWS_REGION", "ap-south-1")

# Slack settings
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#incidents-prod")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")  # optional real webhook

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
