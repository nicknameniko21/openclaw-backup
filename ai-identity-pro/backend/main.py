"""
AI Identity Pro - Backend API
Upgraded from Second-Me with commercial features
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import jwt
import hashlib
import uuid

app = FastAPI(
    title="AI Identity Pro API",
    description="Premium Digital Twin Platform API",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = "your-secret-key-change-in-production"

# In-memory storage (replace with PostgreSQL in production)
users_db = {}
twins_db = {}
conversations_db = {}
api_keys_db = {}

# ============ MODELS ============

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TwinCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    personality_traits: List[str] = []
    knowledge_areas: List[str] = []

class TwinUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    knowledge_areas: Optional[List[str]] = None

class MessageRequest(BaseModel):
    twin_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}

class MemoryAdd(BaseModel):
    twin_id: str
    content: str
    category: str = "general"
    importance: int = Field(1, ge=1, le=10)

class SubscriptionTier(BaseModel):
    tier: str  # free, pro, business, enterprise
    max_twins: int
    max_messages: int
    api_calls: int
    features: List[str]

# ============ SUBSCRIPTION TIERS ============

SUBSCRIPTION_TIERS = {
    "free": SubscriptionTier(
        tier="free",
        max_twins=1,
        max_messages=100,
        api_calls=0,
        features=["basic_memory", "web_chat"]
    ),
    "pro": SubscriptionTier(
        tier="pro",
        max_twins=3,
        max_messages=-1,  # unlimited
        api_calls=1000,
        features=["advanced_memory", "api_access", "email_support", "analytics"]
    ),
    "business": SubscriptionTier(
        tier="business",
        max_twins=10,
        max_messages=-1,
        api_calls=10000,
        features=["priority_api", "custom_integrations", "priority_support", "team_collaboration"]
    ),
    "enterprise": SubscriptionTier(
        tier="enterprise",
        max_twins=-1,
        max_messages=-1,
        api_calls=100000,
        features=["dedicated_infra", "sla", "white_label", "custom_training"]
    )
}

# ============ AUTHENTICATION ============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_subscription(user_id: str, feature: str):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tier = SUBSCRIPTION_TIERS.get(user.get("tier", "free"))
    if feature not in tier.features:
        raise HTTPException(
            status_code=403, 
            detail=f"Feature '{feature}' requires {tier.tier} tier or higher"
        )
    return tier

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "name": "AI Identity Pro API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register new user"""
    if user.email in [u["email"] for u in users_db.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "tier": "free",
        "created_at": datetime.utcnow().isoformat(),
        "api_key": None,
        "message_count": 0,
        "api_call_count": 0
    }
    
    return {
        "user_id": user_id,
        "token": create_token(user_id),
        "tier": "free"
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login user"""
    for user_id, user in users_db.items():
        if user["email"] == credentials.email:
            if user["password_hash"] == hash_password(credentials.password):
                return {
                    "user_id": user_id,
                    "token": create_token(user_id),
                    "tier": user["tier"]
                }
            raise HTTPException(status_code=401, detail="Invalid password")
    
    raise HTTPException(status_code=401, detail="User not found")

@app.get("/api/user/me")
async def get_user(user_id: str = Depends(verify_token)):
    """Get current user info"""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tier = SUBSCRIPTION_TIERS[user["tier"]]
    
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "tier": user["tier"],
        "tier_limits": tier.dict(),
        "message_count": user["message_count"],
        "api_call_count": user["api_call_count"],
        "created_at": user["created_at"]
    }

# ============ TWIN MANAGEMENT ============

@app.post("/api/twins")
async def create_twin(twin: TwinCreate, user_id: str = Depends(verify_token)):
    """Create new digital twin"""
    user = users_db.get(user_id)
    tier = SUBSCRIPTION_TIERS[user["tier"]]
    
    # Check twin limit
    user_twins = [t for t in twins_db.values() if t["user_id"] == user_id]
    if tier.max_twins != -1 and len(user_twins) >= tier.max_twins:
        raise HTTPException(
            status_code=403, 
            detail=f"Maximum {tier.max_twins} twins allowed on {user['tier']} tier"
        )
    
    twin_id = str(uuid.uuid4())
    twins_db[twin_id] = {
        "id": twin_id,
        "user_id": user_id,
        "name": twin.name,
        "description": twin.description,
        "personality_traits": twin.personality_traits,
        "knowledge_areas": twin.knowledge_areas,
        "status": "training",
        "created_at": datetime.utcnow().isoformat(),
        "memory_count": 0,
        "conversation_count": 0
    }
    
    return {
        "twin_id": twin_id,
        "status": "created",
        "training_status": "in_progress"
    }

@app.get("/api/twins")
async def list_twins(user_id: str = Depends(verify_token)):
    """List all user twins"""
    user_twins = [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "status": t["status"],
            "memory_count": t["memory_count"],
            "conversation_count": t["conversation_count"],
            "created_at": t["created_at"]
        }
        for t in twins_db.values()
        if t["user_id"] == user_id
    ]
    return {"twins": user_twins}

@app.get("/api/twins/{twin_id}")
async def get_twin(twin_id: str, user_id: str = Depends(verify_token)):
    """Get twin details"""
    twin = twins_db.get(twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    return twin

@app.put("/api/twins/{twin_id}")
async def update_twin(
    twin_id: str, 
    update: TwinUpdate, 
    user_id: str = Depends(verify_token)
):
    """Update twin"""
    twin = twins_db.get(twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    if update.name:
        twin["name"] = update.name
    if update.description:
        twin["description"] = update.description
    if update.personality_traits:
        twin["personality_traits"] = update.personality_traits
    if update.knowledge_areas:
        twin["knowledge_areas"] = update.knowledge_areas
    
    return {"status": "updated", "twin": twin}

@app.delete("/api/twins/{twin_id}")
async def delete_twin(twin_id: str, user_id: str = Depends(verify_token)):
    """Delete twin"""
    twin = twins_db.get(twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    del twins_db[twin_id]
    return {"status": "deleted"}

# ============ CONVERSATION ============

@app.post("/api/chat")
async def chat(request: MessageRequest, user_id: str = Depends(verify_token)):
    """Chat with digital twin"""
    user = users_db.get(user_id)
    tier = SUBSCRIPTION_TIERS[user["tier"]]
    
    # Check message limit
    if tier.max_messages != -1 and user["message_count"] >= tier.max_messages:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly message limit ({tier.max_messages}) reached"
        )
    
    twin = twins_db.get(request.twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    # Increment message count
    user["message_count"] += 1
    
    # TODO: Integrate with Kimi API for actual response
    # For now, return mock response
    response = {
        "response": f"This is a response from {twin['name']}. In production, this would use Kimi API with the twin's personality and memories.",
        "twin_id": request.twin_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message_count": user["message_count"]
    }
    
    return response

# ============ MEMORY MANAGEMENT ============

@app.post("/api/memories")
async def add_memory(memory: MemoryAdd, user_id: str = Depends(verify_token)):
    """Add memory to twin"""
    check_subscription(user_id, "advanced_memory")
    
    twin = twins_db.get(memory.twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    memory_id = str(uuid.uuid4())
    # Store memory (in production, use vector DB)
    
    twin["memory_count"] += 1
    
    return {
        "memory_id": memory_id,
        "status": "added",
        "twin_memory_count": twin["memory_count"]
    }

@app.get("/api/twins/{twin_id}/memories")
async def get_memories(twin_id: str, user_id: str = Depends(verify_token)):
    """Get twin memories"""
    check_subscription(user_id, "advanced_memory")
    
    twin = twins_db.get(twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    # Return mock memories (in production, query vector DB)
    return {
        "twin_id": twin_id,
        "memories": [],
        "total": twin["memory_count"]
    }

# ============ API KEY MANAGEMENT ============

@app.post("/api/keys")
async def create_api_key(user_id: str = Depends(verify_token)):
    """Create API key"""
    check_subscription(user_id, "api_access")
    
    user = users_db.get(user_id)
    api_key = f"aip_{uuid.uuid4().hex}"
    user["api_key"] = api_key
    
    api_keys_db[api_key] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None
    }
    
    return {
        "api_key": api_key,
        "created_at": api_keys_db[api_key]["created_at"]
    }

@app.get("/api/keys")
async def list_api_keys(user_id: str = Depends(verify_token)):
    """List API keys"""
    check_subscription(user_id, "api_access")
    
    user = users_db.get(user_id)
    if not user.get("api_key"):
        return {"keys": []}
    
    return {
        "keys": [{
            "key": user["api_key"][:20] + "...",
            "created_at": api_keys_db[user["api_key"]]["created_at"],
            "last_used": api_keys_db[user["api_key"]].get("last_used")
        }]
    }

# ============ ANALYTICS ============

@app.get("/api/analytics")
async def get_analytics(user_id: str = Depends(verify_token)):
    """Get user analytics"""
    check_subscription(user_id, "analytics")
    
    user = users_db.get(user_id)
    user_twins = [t for t in twins_db.values() if t["user_id"] == user_id]
    
    return {
        "total_twins": len(user_twins),
        "total_memories": sum(t["memory_count"] for t in user_twins),
        "total_conversations": sum(t["conversation_count"] for t in user_twins),
        "messages_this_month": user["message_count"],
        "api_calls_this_month": user["api_call_count"],
        "tier": user["tier"]
    }

# ============ SUBSCRIPTION ============

@app.get("/api/subscription/tiers")
async def list_tiers():
    """List all subscription tiers"""
    return {
        "tiers": {k: v.dict() for k, v in SUBSCRIPTION_TIERS.items()}
    }

@app.post("/api/subscription/upgrade")
async def upgrade_subscription(
    tier: str, 
    user_id: str = Depends(verify_token)
):
    """Upgrade subscription (mock - integrate with Stripe)"""
    if tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    user = users_db.get(user_id)
    user["tier"] = tier
    
    return {
        "status": "upgraded",
        "tier": tier,
        "features": SUBSCRIPTION_TIERS[tier].features
    }

# ============ PUBLIC API (API KEY AUTH) ============

@app.post("/api/v1/chat")
async def public_chat(
    request: MessageRequest,
    api_key: str
):
    """Public API endpoint for chat (uses API key)"""
    if api_key not in api_keys_db:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_data = api_keys_db[api_key]
    user_id = key_data["user_id"]
    user = users_db.get(user_id)
    
    # Check API call limit
    tier = SUBSCRIPTION_TIERS[user["tier"]]
    if tier.api_calls != -1 and user["api_call_count"] >= tier.api_calls:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly API call limit ({tier.api_calls}) reached"
        )
    
    # Increment API call count
    user["api_call_count"] += 1
    key_data["last_used"] = datetime.utcnow().isoformat()
    
    twin = twins_db.get(request.twin_id)
    if not twin or twin["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Twin not found")
    
    # TODO: Integrate with Kimi API
    return {
        "response": f"API response from {twin['name']}",
        "twin_id": request.twin_id,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
