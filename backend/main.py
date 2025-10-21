# backend/main.py

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Load environment variables first
load_dotenv()


# --- Auth Setup ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
SIMPLE_AUTH_USERNAME = os.getenv("SIMPLE_AUTH_USERNAME")
SIMPLE_AUTH_PASSWORD_HASH = os.getenv("SIMPLE_AUTH_PASSWORD_HASH")

if not all([JWT_SECRET_KEY, SIMPLE_AUTH_USERNAME, SIMPLE_AUTH_PASSWORD_HASH]):
    print("❌ Auth environment variables are not set. Exiting.", file=sys.stderr)
    sys.exit(1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- ADK Setup ---
from google.adk.cli.fast_api import get_fast_api_app
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=False,
)

app.title = "Rumi-Analytica Backend"
app.description = "Backend for the multi-agent analytics platform."


# --- CORS Middleware ---
# Base origins for local development
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite dev server
]

# Dynamically add the deployed frontend URL from an environment variable
# This variable will be set by Cloud Build when deploying to Cloud Run.
deployed_frontend_url = os.getenv("FRONTEND_URL")
if deployed_frontend_url:
    origins.append(deployed_frontend_url)
    print(f"✅ Added deployed frontend URL to CORS origins: {deployed_frontend_url}", file=sys.stderr)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper Functions ---
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
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != SIMPLE_AUTH_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}


# --- Pydantic Models for Data Transformation ---
class FrontendChatRequest(BaseModel):
    message: str

class ADKChatRequest(BaseModel):
    query: str


# --- Login Endpoint ---
@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if form_data.username != SIMPLE_AUTH_USERNAME or not verify_password(form_data.password, SIMPLE_AUTH_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Secure and Proxy ADK Chat Endpoint ---
adk_chat_endpoint = None

for route in app.routes:
    if route.path == "/agent/{agent_name}/chat" and "POST" in route.methods:
        adk_chat_endpoint = route.endpoint
        app.post("/agent/{agent_name}/chat", dependencies=[Depends(get_current_user)])(adk_chat_endpoint)
        print(f"✅ Secured ADK route: {route.path}", file=sys.stderr)
        break

@app.post("/api/chat")
async def proxy_chat(
    frontend_request: FrontendChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not adk_chat_endpoint:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")
    
    agent_name = "analytica_agent"
    adk_request = ADKChatRequest(query=frontend_request.message)
    adk_response = await adk_chat_endpoint(agent_name=agent_name, request=adk_request)
    
    try:
        ai_text = adk_response.get("response", {}).get("output")
        if ai_text is None:
           ai_text = "Sorry, I received an empty response."
    except (AttributeError, TypeError):
        ai_text = "Sorry, I encountered an error processing the response."

    return {"response": ai_text}

print("✅ Configured proxy route /api/chat with request/response transformation.", file=sys.stderr)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

print("🚀 Rumi-Analytica Backend starting up...", file=sys.stderr)