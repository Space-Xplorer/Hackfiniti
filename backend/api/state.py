import uuid

# In-memory stores
USERS_DB = {}          # email -> { id, email, password, name, role }
APPLICATIONS_DB = {}   # app_id -> full application object
WORKFLOW_DB = {}       # app_id -> workflow result object
WORKFLOW_EVENTS = {}   # app_id -> list of { agent, status }


def create_token(email: str) -> str:
    return f"token::{email}"


def parse_token(token: str):
    """Extract email from 'token::<email>' format. Returns None if invalid."""
    if token and token.startswith("token::"):
        return token[len("token::"):]
    return None


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"