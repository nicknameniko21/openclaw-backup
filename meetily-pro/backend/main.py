"""
Meetily Pro - Enterprise Meeting Intelligence API
Upgraded from Meetily with commercial features
"""

from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import jwt
import hashlib
import uuid
import asyncio

app = FastAPI(
    title="Meetily Pro API",
    description="Enterprise Meeting Intelligence Platform",
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
organizations_db = {}
users_db = {}
meetings_db = {}
transcripts_db = {}
summaries_db = {}
teams_db = {}
integrations_db = {}
api_keys_db = {}
audit_logs_db = []

# ============ ENUMS ============

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ComplianceStandard(str, Enum):
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    ISO27001 = "iso27001"

# ============ MODELS ============

class OrganizationCreate(BaseModel):
    name: str
    domain: str
    tier: SubscriptionTier = SubscriptionTier.STARTER
    compliance_standards: List[ComplianceStandard] = []

class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    organization_id: str
    role: str = "member"  # admin, member, viewer

class UserLogin(BaseModel):
    email: str
    password: str

class MeetingCreate(BaseModel):
    title: str
    scheduled_at: datetime
    participants: List[str] = []
    calendar_event_id: Optional[str] = None

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    participants: Optional[List[str]] = None

class SummaryTemplate(BaseModel):
    name: str
    template: str
    sections: List[str]

class IntegrationConfig(BaseModel):
    provider: str  # slack, teams, zoom, calendar
    config: Dict[str, Any]

class AuditLogEntry(BaseModel):
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]

# ============ SUBSCRIPTION TIERS ============

SUBSCRIPTION_LIMITS = {
    SubscriptionTier.STARTER: {
        "max_users": 10,
        "max_meetings_per_month": 100,
        "storage_gb": 10,
        "retention_days": 30,
        "features": ["transcription", "basic_summary", "email_support"]
    },
    SubscriptionTier.PROFESSIONAL: {
        "max_users": 50,
        "max_meetings_per_month": 500,
        "storage_gb": 100,
        "retention_days": 365,
        "features": [
            "transcription", "advanced_summary", "custom_templates",
            "calendar_integration", "slack_integration", "analytics",
            "priority_support"
        ]
    },
    SubscriptionTier.ENTERPRISE: {
        "max_users": -1,  # unlimited
        "max_meetings_per_month": -1,
        "storage_gb": 1000,
        "retention_days": -1,  # unlimited
        "features": [
            "transcription", "advanced_summary", "custom_templates",
            "calendar_integration", "slack_integration", "teams_integration",
            "zoom_integration", "analytics", "api_access", "sso",
            "audit_logs", "on_premise", "dedicated_support"
        ]
    },
    SubscriptionTier.CUSTOM: {
        "max_users": -1,
        "max_meetings_per_month": -1,
        "storage_gb": -1,
        "retention_days": -1,
        "features": ["all"]
    }
}

# ============ AUTHENTICATION ============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str, org_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "organization_id": org_id,
        "role": role,
        "exp": datetime.utcnow().timestamp() + 86400
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_permission(token_data: Dict, required_role: str):
    role_hierarchy = {"viewer": 0, "member": 1, "admin": 2}
    if role_hierarchy.get(token_data["role"], 0) < role_hierarchy.get(required_role, 0):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

def log_audit(user_id: str, action: str, resource_type: str, resource_id: str, details: Dict = {}):
    audit_logs_db.append({
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details
    })

# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "name": "Meetily Pro API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "enterprise": True
    }

# ============ ORGANIZATION MANAGEMENT ============

@app.post("/api/organizations")
async def create_organization(org: OrganizationCreate):
    """Create new organization"""
    org_id = str(uuid.uuid4())
    
    organizations_db[org_id] = {
        "id": org_id,
        "name": org.name,
        "domain": org.domain,
        "tier": org.tier.value,
        "compliance_standards": [s.value for s in org.compliance_standards],
        "created_at": datetime.utcnow().isoformat(),
        "meeting_count": 0,
        "storage_used_gb": 0,
        "billing_email": None,
        "stripe_customer_id": None
    }
    
    return {
        "organization_id": org_id,
        "status": "created",
        "tier": org.tier.value
    }

@app.get("/api/organizations/{org_id}")
async def get_organization(
    org_id: str,
    token: Dict = Depends(verify_token)
):
    """Get organization details"""
    if token["organization_id"] != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    org = organizations_db.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    tier_limits = SUBSCRIPTION_LIMITS[SubscriptionTier(org["tier"])]
    
    return {
        **org,
        "limits": tier_limits,
        "usage": {
            "meetings_this_month": org["meeting_count"],
            "storage_used_gb": org["storage_used_gb"]
        }
    }

# ============ USER MANAGEMENT ============

@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register new user"""
    org = organizations_db.get(user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check user limit
    tier_limits = SUBSCRIPTION_LIMITS[SubscriptionTier(org["tier"])]
    org_users = [u for u in users_db.values() if u["organization_id"] == user.organization_id]
    if tier_limits["max_users"] != -1 and len(org_users) >= tier_limits["max_users"]:
        raise HTTPException(status_code=403, detail="User limit reached for tier")
    
    if user.email in [u["email"] for u in users_db.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "id": user_id,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "name": user.name,
        "organization_id": user.organization_id,
        "role": user.role,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None,
        "api_key": None
    }
    
    log_audit(user_id, "user_created", "user", user_id, {"email": user.email})
    
    return {
        "user_id": user_id,
        "token": create_token(user_id, user.organization_id, user.role),
        "organization_id": user.organization_id
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login user"""
    for user_id, user in users_db.items():
        if user["email"] == credentials.email:
            if user["password_hash"] == hash_password(credentials.password):
                user["last_login"] = datetime.utcnow().isoformat()
                log_audit(user_id, "user_login", "user", user_id, {})
                return {
                    "user_id": user_id,
                    "token": create_token(user_id, user["organization_id"], user["role"]),
                    "organization_id": user["organization_id"],
                    "role": user["role"]
                }
            raise HTTPException(status_code=401, detail="Invalid password")
    
    raise HTTPException(status_code=401, detail="User not found")

@app.get("/api/users/me")
async def get_current_user(token: Dict = Depends(verify_token)):
    """Get current user info"""
    user = users_db.get(token["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    org = organizations_db.get(user["organization_id"])
    tier_limits = SUBSCRIPTION_LIMITS[SubscriptionTier(org["tier"])]
    
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "organization": {
            "id": org["id"],
            "name": org["name"],
            "tier": org["tier"],
            "limits": tier_limits
        }
    }

# ============ MEETING MANAGEMENT ============

@app.post("/api/meetings")
async def create_meeting(
    meeting: MeetingCreate,
    token: Dict = Depends(verify_token)
):
    """Schedule new meeting"""
    org = organizations_db.get(token["organization_id"])
    tier_limits = SUBSCRIPTION_LIMITS[SubscriptionTier(org["tier"])]
    
    # Check meeting limit
    if tier_limits["max_meetings_per_month"] != -1:
        if org["meeting_count"] >= tier_limits["max_meetings_per_month"]:
            raise HTTPException(status_code=403, detail="Monthly meeting limit reached")
    
    meeting_id = str(uuid.uuid4())
    meetings_db[meeting_id] = {
        "id": meeting_id,
        "organization_id": token["organization_id"],
        "created_by": token["user_id"],
        "title": meeting.title,
        "scheduled_at": meeting.scheduled_at.isoformat(),
        "participants": meeting.participants,
        "calendar_event_id": meeting.calendar_event_id,
        "status": MeetingStatus.SCHEDULED.value,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "ended_at": None,
        "duration_seconds": None,
        "recording_url": None,
        "transcript_id": None,
        "summary_id": None
    }
    
    org["meeting_count"] += 1
    log_audit(token["user_id"], "meeting_created", "meeting", meeting_id, {"title": meeting.title})
    
    return {
        "meeting_id": meeting_id,
        "status": "scheduled"
    }

@app.get("/api/meetings")
async def list_meetings(
    status: Optional[str] = None,
    token: Dict = Depends(verify_token)
):
    """List organization meetings"""
    org_meetings = [
        m for m in meetings_db.values()
        if m["organization_id"] == token["organization_id"]
    ]
    
    if status:
        org_meetings = [m for m in org_meetings if m["status"] == status]
    
    return {
        "meetings": sorted(org_meetings, key=lambda x: x["scheduled_at"], reverse=True),
        "total": len(org_meetings)
    }

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    token: Dict = Depends(verify_token)
):
    """Get meeting details"""
    meeting = meetings_db.get(meeting_id)
    if not meeting or meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    result = {**meeting}
    
    # Add transcript if available
    if meeting.get("transcript_id"):
        transcript = transcripts_db.get(meeting["transcript_id"])
        if transcript:
            result["transcript"] = transcript
    
    # Add summary if available
    if meeting.get("summary_id"):
        summary = summaries_db.get(meeting["summary_id"])
        if summary:
            result["summary"] = summary
    
    return result

@app.post("/api/meetings/{meeting_id}/start")
async def start_meeting(
    meeting_id: str,
    token: Dict = Depends(verify_token)
):
    """Start meeting recording"""
    meeting = meetings_db.get(meeting_id)
    if not meeting or meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting["status"] = MeetingStatus.LIVE.value
    meeting["started_at"] = datetime.utcnow().isoformat()
    
    log_audit(token["user_id"], "meeting_started", "meeting", meeting_id, {})
    
    return {"status": "recording_started"}

@app.post("/api/meetings/{meeting_id}/stop")
async def stop_meeting(
    meeting_id: str,
    token: Dict = Depends(verify_token)
):
    """Stop meeting and trigger processing"""
    meeting = meetings_db.get(meeting_id)
    if not meeting or meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting["status"] = MeetingStatus.PROCESSING.value
    meeting["ended_at"] = datetime.utcnow().isoformat()
    
    # Calculate duration
    if meeting["started_at"]:
        start = datetime.fromisoformat(meeting["started_at"])
        end = datetime.fromisoformat(meeting["ended_at"])
        meeting["duration_seconds"] = (end - start).total_seconds()
    
    log_audit(token["user_id"], "meeting_ended", "meeting", meeting_id, {})
    
    # TODO: Trigger async transcription and summarization
    
    return {
        "status": "processing",
        "meeting_id": meeting_id,
        "estimated_processing_time": "2-5 minutes"
    }

# ============ TRANSCRIPTION ============

@app.post("/api/meetings/{meeting_id}/transcribe")
async def transcribe_meeting(
    meeting_id: str,
    audio_file: UploadFile = File(...),
    token: Dict = Depends(verify_token)
):
    """Upload and transcribe meeting audio"""
    meeting = meetings_db.get(meeting_id)
    if not meeting or meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript_id = str(uuid.uuid4())
    
    # TODO: Process audio with Whisper
    # For now, return mock transcript
    transcripts_db[transcript_id] = {
        "id": transcript_id,
        "meeting_id": meeting_id,
        "status": "processing",
        "segments": [],
        "full_text": "",
        "speakers": [],
        "language": "en",
        "created_at": datetime.utcnow().isoformat()
    }
    
    meeting["transcript_id"] = transcript_id
    
    return {
        "transcript_id": transcript_id,
        "status": "processing"
    }

@app.get("/api/transcripts/{transcript_id}")
async def get_transcript(
    transcript_id: str,
    token: Dict = Depends(verify_token)
):
    """Get transcript"""
    transcript = transcripts_db.get(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    meeting = meetings_db.get(transcript["meeting_id"])
    if meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return transcript

# ============ SUMMARIZATION ============

@app.post("/api/meetings/{meeting_id}/summarize")
async def summarize_meeting(
    meeting_id: str,
    template_id: Optional[str] = None,
    token: Dict = Depends(verify_token)
):
    """Generate meeting summary"""
    meeting = meetings_db.get(meeting_id)
    if not meeting or meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.get("transcript_id"):
        raise HTTPException(status_code=400, detail="Transcript required")
    
    summary_id = str(uuid.uuid4())
    
    # TODO: Generate summary using Kimi API
    summaries_db[summary_id] = {
        "id": summary_id,
        "meeting_id": meeting_id,
        "template_id": template_id,
        "status": "processing",
        "content": None,
        "key_points": [],
        "action_items": [],
        "decisions": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    meeting["summary_id"] = summary_id
    
    return {
        "summary_id": summary_id,
        "status": "processing"
    }

@app.get("/api/summaries/{summary_id}")
async def get_summary(
    summary_id: str,
    token: Dict = Depends(verify_token)
):
    """Get summary"""
    summary = summaries_db.get(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    meeting = meetings_db.get(summary["meeting_id"])
    if meeting["organization_id"] != token["organization_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return summary

# ============ TEMPLATES ============

@app.post("/api/templates")
async def create_template(
    template: SummaryTemplate,
    token: Dict = Depends(verify_token)
):
    """Create custom summary template"""
    check_permission(token, "admin")
    
    template_id = str(uuid.uuid4())
    
    return {
        "template_id": template_id,
        "status": "created"
    }

# ============ ANALYTICS ============

@app.get("/api/analytics/organization")
async def get_organization_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: Dict = Depends(verify_token)
):
    """Get organization analytics"""
    org_id = token["organization_id"]
    org = organizations_db.get(org_id)
    
    org_meetings = [m for m in meetings_db.values() if m["organization_id"] == org_id]
    
    total_duration = sum(
        m.get("duration_seconds", 0) or 0 
        for m in org_meetings
    )
    
    return {
        "total_meetings": len(org_meetings),
        "completed_meetings": len([m for m in org_meetings if m["status"] == "completed"]),
        "total_duration_hours": total_duration / 3600,
        "average_meeting_duration_minutes": (total_duration / len(org_meetings) / 60) if org_meetings else 0,
        "storage_used_gb": org["storage_used_gb"],
        "active_users": len([u for u in users_db.values() if u["organization_id"] == org_id]),
        "period": {
            "start": start_date,
            "end": end_date
        }
    }

@app.get("/api/analytics/meetings/trends")
async def get_meeting_trends(
    days: int = 30,
    token: Dict = Depends(verify_token)
):
    """Get meeting trends over time"""
    org_id = token["organization_id"]
    
    # TODO: Aggregate meeting data by day
    
    return {
        "period_days": days,
        "daily_stats": []
    }

# ============ INTEGRATIONS ============

@app.post("/api/integrations")
async def create_integration(
    integration: IntegrationConfig,
    token: Dict = Depends(verify_token)
):
    """Configure integration"""
    check_permission(token, "admin")
    
    integration_id = str(uuid.uuid4())
    integrations_db[integration_id] = {
        "id": integration_id,
        "organization_id": token["organization_id"],
        "provider": integration.provider,
        "config": integration.config,
        "status": "connected",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "integration_id": integration_id,
        "status": "connected"
    }

@app.get("/api/integrations")
async def list_integrations(token: Dict = Depends(verify_token)):
    """List organization integrations"""
    org_integrations = [
        i for i in integrations_db.values()
        if i["organization_id"] == token["organization_id"]
    ]
    
    return {"integrations": org_integrations}

# ============ AUDIT LOGS ============

@app.get("/api/audit-logs")
async def get_audit_logs(
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    token: Dict = Depends(verify_token)
):
    """Get audit logs (admin only)"""
    check_permission(token, "admin")
    
    logs = [
        log for log in audit_logs_db
        if log["user_id"] in [u["id"] for u in users_db.values() 
                             if u["organization_id"] == token["organization_id"]]
    ]
    
    if resource_type:
        logs = [l for l in logs if l["resource_type"] == resource_type]
    
    if user_id:
        logs = [l for l in logs if l["user_id"] == user_id]
    
    return {
        "logs": logs[-limit:],
        "total": len(logs)
    }

# ============ WEBSOCKET FOR REAL-TIME ============

@app.websocket("/ws/meetings/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    """WebSocket for real-time meeting updates"""
    await websocket.accept()
    
    try:
        while True:
            # TODO: Handle real-time transcription updates
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
