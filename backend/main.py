# backend/main.py

import os
import sys
import json
import httpx
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# --- Load environment variables ---
load_dotenv()

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

# --- ADK setup ---
from google.adk.cli.fast_api import get_fast_api_app

# The name of the folder containing your agent.py
# Example: ./agents/analytica_agent/agent.py -> app_name is 'analytica_agent'
AGENT_APP_NAME = "agent" 

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
app: FastAPI = get_fast_api_app(
    agents_dir=os.path.join(AGENT_DIR, "agents"), # Point to the directory containing agent folders
    web=False,
)

app.title = "Rumi-Analytica Backend"

# --- CORS setup ---
origins = [
    "http://localhost:3000", 
    "http://localhost:5173",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth helpers ---
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

# --- Models ---
class FrontendChatRequest(BaseModel):
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- Auth endpoint ---
@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if form_data.username != SIMPLE_AUTH_USERNAME or not verify_password(form_data.password, SIMPLE_AUTH_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- CORRECTED Chat endpoint ---
@app.post("/api/chat")
async def proxy_chat(
    frontend_request: FrontendChatRequest,
    request: Request, # Get the original request to build the full URL
    current_user: dict = Depends(get_current_user)
):
    # This is the URL to the ADK endpoint on THIS server
    run_sse_url = f"{request.base_url}run_sse"
    
    # The user_id can be derived from your auth system
    user_id = current_user["username"]
    # A session_id is required. We'll use a static one for simplicity.
    session_id = "default_session"

    # Construct the payload required by the ADK /run_sse endpoint
    adk_payload = {
        "app_name": AGENT_APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": frontend_request.message}]
        },
        "streaming": True # ADK requires handling the stream
    }

    final_response_text = ""
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", run_sse_url, json=adk_payload, timeout=60.0) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise HTTPException(status_code=response.status_code, detail=f"ADK Error: {error_text.decode()}")

                # Process the Server-Sent Events (SSE) stream
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        try:
                            # Clean the line to get the JSON data
                            data_str = line[len('data: '):]
                            if data_str:
                                event_data = json.loads(data_str)
                                # The final output is in the event with state "DONE"
                                if event_data.get("state") == "DONE":
                                    final_response_text = event_data.get("response", {}).get("output", "No output found in final event.")
                                    break # We have the final answer, exit the loop
                        except json.JSONDecodeError:
                            # Incomplete JSON chunk, just continue to the next line
                            continue
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error calling ADK service: {e}")

    if not final_response_text:
        final_response_text = "Sorry, I could not get a response from the agent."

    return {"response": final_response_text}

# --- Health check ---
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- FIX: Hide ADK routes from docs ---
for route in app.routes:
    # Check if the route has an endpoint and if that endpoint has a __module__
    if hasattr(route, "endpoint") and hasattr(route.endpoint, "__module__"):
        # If the route's code is from the google.adk library, hide it
        if route.endpoint.__module__.startswith("google.adk"):
            route.include_in_schema = False
