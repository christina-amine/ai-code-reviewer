"""
GitHub OAuth client and server-side session store.

The OAuth handshake itself relies on Starlette's SessionMiddleware (a signed
cookie) to hold transient state/nonce values. Once a user authorizes, their
GitHub access token is kept server-side in `_sessions`, keyed by an opaque
session id handed back to the frontend - the token itself never leaves the
backend.
"""

import secrets
from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth

from config import settings

oauth = OAuth()

oauth.register(
    name="github",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "repo read:user"},
)

# In-memory session store: session_id -> {"access_token": ..., "user": {...}}
# In production, replace with a shared store (e.g. Redis) so sessions survive
# restarts and work across multiple backend instances.
_sessions: Dict[str, Dict[str, Any]] = {}


def create_session(access_token: str, user: Dict[str, Any]) -> str:
    """Store a new authenticated session and return its opaque id."""
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {"access_token": access_token, "user": user}
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Look up a session by id, or None if it doesn't exist."""
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session, e.g. on logout."""
    _sessions.pop(session_id, None)
