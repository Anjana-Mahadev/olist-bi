import os
import multiprocessing

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Workers — 2-4x CPU cores is typical; for LLM-bound I/O work, more workers help
workers = int(os.getenv("GUNICORN_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 4)))

# Timeout — LLM calls can be slow
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Graceful restart
graceful_timeout = 30
