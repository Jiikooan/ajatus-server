"""
Ajatuskumppani Backend API Server
FastAPI backend with Fireworks AI, MCP code execution, and Stripe payments
"""

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json
import asyncio
from datetime import datetime
import stripe
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fireworks AI client
try:
    from fireworks.client import Fireworks
    FIREWORKS_AVAILABLE = True
except ImportError:
    FIREWORKS_AVAILABLE = False
    logger.warning("Fireworks AI not installed. Install with: pip install fireworks-ai")

app = FastAPI(
    title="Ajatuskumppani API",
    description="Finnish-first open-source decentralized AI platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.manus.space",
        "https://*.manusvm.computer"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # For AJT token product

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logger.info("Stripe initialized")

# Initialize Fireworks client
fireworks_client = None
if FIREWORKS_AVAILABLE and FIREWORKS_API_KEY:
    fireworks_client = Fireworks(api_key=FIREWORKS_API_KEY)
    logger.info("Fireworks AI initialized")

# ==================== Pydantic Models ====================

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation history")
    model: str = Field(
        default="accounts/fireworks/models/llama-v4-maverick",
        description="Fireworks AI model to use"
    )
    stream: bool = Field(default=True, description="Enable streaming responses")
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    wallet_address: Optional[str] = Field(None, description="Solana wallet address for AJT deduction")

class ExecuteCodeRequest(BaseModel):
    code: str = Field(..., description="Code to execute")
    language: str = Field(default="python", description="Programming language")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")

class CreateCheckoutRequest(BaseModel):
    amount: int = Field(..., ge=1000, description="AJT tokens to purchase (minimum 1000)")
    currency: str = Field(default="usd")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")
    wallet_address: str = Field(..., description="Solana wallet address to credit tokens")

class BalanceResponse(BaseModel):
    wallet_address: str
    balance: int
    consumed: int
    last_updated: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    fireworks_available: bool
    stripe_configured: bool
    timestamp: str

# ==================== In-Memory Storage ====================
# TODO: Replace with PostgreSQL/Redis in production

user_balances: Dict[str, Dict[str, Any]] = {}

# ==================== Helper Functions ====================

def get_user_balance(wallet_address: str) -> Dict[str, Any]:
    """Get or create user balance"""
    if wallet_address not in user_balances:
        user_balances[wallet_address] = {
            "balance": 1000,  # Initial free credits
            "consumed": 0,
            "last_updated": datetime.now().isoformat()
        }
    return user_balances[wallet_address]

def deduct_ajt(wallet_address: str, amount: int) -> bool:
    """Deduct AJT tokens from user balance"""
    balance = get_user_balance(wallet_address)
    if balance["balance"] < amount:
        return False
    
    balance["balance"] -= amount
    balance["consumed"] += amount
    balance["last_updated"] = datetime.now().isoformat()
    user_balances[wallet_address] = balance
    return True

def add_ajt(wallet_address: str, amount: int):
    """Add AJT tokens to user balance"""
    balance = get_user_balance(wallet_address)
    balance["balance"] += amount
    balance["last_updated"] = datetime.now().isoformat()
    user_balances[wallet_address] = balance

# ==================== API Endpoints ====================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="online",
        service="Ajatuskumppani API",
        version="1.0.0",
        fireworks_available=fireworks_client is not None,
        stripe_configured=bool(STRIPE_SECRET_KEY),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming support using Fireworks AI
    Consumes 1 AJT per message
    """
    if not fireworks_client:
        raise HTTPException(
            status_code=503,
            detail="Fireworks AI not configured. Please set FIREWORKS_API_KEY environment variable."
        )
    
    # Check and deduct AJT balance
    if request.wallet_address:
        if not deduct_ajt(request.wallet_address, 1):
            raise HTTPException(
                status_code=402,
                detail="Insufficient AJT balance. Please purchase more tokens."
            )
        logger.info(f"Deducted 1 AJT from {request.wallet_address}")
    
    try:
        # Convert messages to Fireworks format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        if request.stream:
            # Streaming response with Server-Sent Events
            async def generate():
                try:
                    response = fireworks_client.chat.completions.create(
                        model=request.model,
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        stream=True
                    )
                    
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Streaming error: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response
            response = fireworks_client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": request.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if hasattr(response, 'usage') else None
            }
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/api/execute-code")
async def execute_code(request: ExecuteCodeRequest):
    """
    Execute code in a sandboxed environment
    TODO: Implement Docker sandbox execution with MCP
    """
    logger.info(f"Code execution request: {request.language}")
    
    # For now, return a mock response
    # In production, this should use Docker containers or MCP for safe execution
    return {
        "status": "not_implemented",
        "message": "Code execution will be implemented with Docker sandbox",
        "language": request.language,
        "code_length": len(request.code)
    }

@app.get("/api/balance", response_model=BalanceResponse)
async def get_balance(wallet_address: str):
    """Get user's AJT token balance"""
    if not wallet_address:
        raise HTTPException(status_code=400, detail="wallet_address is required")
    
    balance = get_user_balance(wallet_address)
    
    return BalanceResponse(
        wallet_address=wallet_address,
        balance=balance["balance"],
        consumed=balance["consumed"],
        last_updated=balance["last_updated"]
    )

@app.post("/api/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutRequest):
    """Create Stripe checkout session for AJT token purchase"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured. Please set STRIPE_SECRET_KEY environment variable."
        )
    
    try:
        # Calculate price: 1000 AJT = $1 USD
        price_in_cents = int((request.amount / 1000) * 100)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": request.currency,
                    "product_data": {
                        "name": f"{request.amount:,} AJT Tokens",
                        "description": "Ajatuskumppani AI Credits",
                        "images": ["https://ajatuskumppani.manus.space/logo.png"]
                    },
                    "unit_amount": price_in_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{request.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url,
            metadata={
                "wallet_address": request.wallet_address,
                "ajt_amount": str(request.amount)
            }
        )
        
        logger.info(f"Created checkout session {session.id} for {request.wallet_address}")
        
        return {
            "sessionId": session.id,
            "url": session.url
        }
    
    except Exception as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

@app.post("/api/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment verification"""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Stripe webhook not configured"
        )
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        wallet_address = session["metadata"]["wallet_address"]
        ajt_amount = int(session["metadata"]["ajt_amount"])
        
        # Credit user's AJT balance
        add_ajt(wallet_address, ajt_amount)
        logger.info(f"Credited {ajt_amount} AJT to {wallet_address}")
        
        return {"status": "success", "credited": ajt_amount}
    
    return {"status": "ignored", "type": event["type"]}

# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("Ajatuskumppani API Server Starting")
    logger.info("=" * 60)
    logger.info(f"Fireworks AI: {'✓ Configured' if fireworks_client else '✗ Not configured'}")
    logger.info(f"Stripe: {'✓ Configured' if STRIPE_SECRET_KEY else '✗ Not configured'}")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

