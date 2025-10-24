# backend/main.py

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from ag_ui_adk import ADKAgent
from agents.agent import root_agent as fmy_llm_agent

# --- Load environment variables ---
load_dotenv()

# Ensure you have GOOGLE_API_KEY in your .env file
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY environment variable is not set. Exiting.", file=sys.stderr)
    sys.exit(1)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
SIMPLE_AUTH_USERNAME = os.getenv("SIMPLE_AUTH_USERNAME")
SIMPLE_AUTH_PASSWORD_HASH = os.getenv("SIMPLE_AUTH_PASSWORD_HASH")

if not all([JWT_SECRET_KEY, SIMPLE_AUTH_USERNAME, SIMPLE_AUTH_PASSWORD_HASH]):
    print("❌ Auth environment variables are not set. Exiting.", file=sys.stderr)
    sys.exit(1)

# --- Use a standard FastAPI app, NOT get_fast_api_app ---
app = FastAPI(title="Rumi-Analytica Backend")
router = APIRouter()

AGENT_APP_NAME = "agent"

# --- CORS setup (no changes) ---
origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth helpers and models (no changes) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != SIMPLE_AUTH_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- Define routes on our router ---
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    if (form_data.username != SIMPLE_AUTH_USERNAME or 
        not verify_password(form_data.password, SIMPLE_AUTH_PASSWORD_HASH)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- REVISED CHAT ENDPOINT ---
@router.post("/api/chat")
async def chat_handler(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Handles chat requests by wrapping the ADK agent and delegating the request.
    This correctly integrates authentication with the AG-UI protocol.
    """
    user_id = current_user["username"]

    # 1. Create an ADKAgent wrapper instance FOR THIS REQUEST.
    #    This correctly associates the authenticated user_id with the agent session.
    adk_agent_wrapper = ADKAgent(
        adk_agent=my_llm_agent,
        app_name=AGENT_APP_NAME,
        user_id=user_id,
        session_timeout_seconds=3600,
        use_in_memory_services=True # This handles session management internally
    )

    # 2. Delegate the raw FastAPI request to the wrapper.
    #    The wrapper will handle the entire AG-UI protocol, including
    #    parsing the request, managing the session, calling the LLM,
    #    and returning a proper StreamingResponse.
    return await adk_agent_wrapper.handle_request(request)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# --- Include router in app ---
app.include_router(router)