from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

mongo = PyMongo()

# In-memory counters are per worker process; fine for the single gunicorn worker
# the Procfile starts. Set RATELIMIT_STORAGE_URI (e.g. a redis:// URL) to share them.
limiter = Limiter(key_func=get_remote_address)

csrf = CSRFProtect()
