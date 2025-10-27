import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

# --- Your existing ADK agent definition ---
from agents.agent.agent import root_agent as agent

# --- Load Environment Variables ---
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
SIMPLE_AUTH_USERNAME = os.getenv("SIMPLE_AUTH_USERNAME")
SIMPLE_AUTH_PASSWORD_HASH = os.getenv("SIMPLE_AUTH_PASSWORD_HASH")
ALGORITHM = "HS256"

if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY is not set. Exiting.", file=sys.stderr); sys.exit(1)
if not all([JWT_SECRET_KEY, SIMPLE_AUTH_USERNAME, SIMPLE_AUTH_PASSWORD_HASH]):
    print("❌ Auth env vars are not set. Exiting.", file=sys.stderr); sys.exit(1)

# --- FastAPI App and Router Setup ---
app = FastAPI(title="Rumi-Analytica Backend")
router = APIRouter()

# --- CORS Middleware ---
origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Create a shared session service instance ---
session_service = InMemorySessionService()
AGENT_APP_NAME = "agent"

# --- Authentication Helpers ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None or username != SIMPLE_AUTH_USERNAME: raise unauthorized
    except JWTError:
        raise unauthorized
    return {"username": username}

# --- API Models ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class SimpleChatRequest(BaseModel):
    message: str

class SimpleChatResponse(BaseModel):
    response: str

# --- API Routes ---
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if (form_data.username != SIMPLE_AUTH_USERNAME or not verify_password(form_data.password, SIMPLE_AUTH_PASSWORD_HASH)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- REVISED CHAT LOGIC USING THE RUNNER PATTERN ---
@router.post("/api/chat", response_model=SimpleChatResponse)
async def simple_chat(
    chat_request: SimpleChatRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["username"]
    session_id = f"{user_id}_default_session"

    # Get or create the session (this part was already correct)
    session = await session_service.get_session(
        app_name=AGENT_APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=AGENT_APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

    # 1. Create a Runner instance
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name=AGENT_APP_NAME
    )

    # 2. Format the message using Content and Part objects
    adk_message = Content(role="user", parts=[Part(text=chat_request.message)])

    response_text = ""
    try:
        # 3. Use runner.run_async and iterate to find the final response
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=adk_message
        ):
            if event.is_final_response():
                # Assuming the final response has at least one text part
                response_text = event.content.parts[0].text
                break # Exit the loop once we have the final answer

    except Exception as e:
        print(f"Error during ADK run: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Error communicating with the agent.")

    if not response_text:
        # Handle cases where the agent might not produce a final response
        raise HTTPException(status_code=500, detail="Agent did not produce a final response.")

    return {"response": response_text}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- Include the router in the app ---
app.include_router(router)