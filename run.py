# backend/run.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Pure & Desi API",
    description="Premium Cold-Pressed Oil E-commerce Platform",
    version="1.0.0",
    # ✅ Disable automatic redirect for trailing slashes
    redirect_slashes=False,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ Define allowed origins clearly
ALLOWED_ORIGINS = [
    # Production - Vercel Frontend
    "https://frontend-mocha-three-41.vercel.app",
    # Production - Main Domain
    "https://thepureanddesi.com",
    "https://www.thepureanddesi.com",
    # Backend domain (for testing)
    "https://api.thepureanddesi.com",
    # Development
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ✅ Custom middleware to handle CORS preflight and prevent redirect issues
@app.middleware("http")
async def cors_preflight_handler(request: Request, call_next):
    """
    Handle CORS preflight requests and add proper headers
    """
    origin = request.headers.get("origin", "")
    
    # Handle OPTIONS (preflight) requests explicitly
    if request.method == "OPTIONS":
        if origin in ALLOWED_ORIGINS:
            return JSONResponse(
                content={},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                }
            )
    
    # Process request
    response = await call_next(request)
    
    # Add CORS headers to actual response
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    
    return response

# Import routers
from app.api.routes import products, orders, contact, delivery, payments, whatsapp, admin
from app.api.routes import auth

# ✅ Include Routers - NO trailing slashes
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(delivery.router, prefix="/api", tags=["Delivery"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pure & Desi API",
        "status": "running",
        "version": "1.0.0",
        "platform": "Render" if os.getenv("RENDER") else "Local",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Pure & Desi API",
        "version": "1.0.0",
        "database": "connected"
    }

@app.get("/api")
async def api_info():
    return {
        "message": "Pure & Desi API Endpoints",
        "version": "1.0.0",
        "endpoints": {
            "products": "/api/products",
            "orders": "/api/orders",
            "delivery": "/api/delivery",
            "payments": "/api/payments",
            "whatsapp": "/api/whatsapp",
            "contact": "/api/contact",
            "auth": "/api/auth",
            "admin": "/api/admin"
        },
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    print("=" * 80)
    print("🚀 Pure & Desi API Starting...")
    print("=" * 80)
    
    # Environment info
    env = "Production (Render)" if os.getenv("RENDER") else "Development"
    port = os.getenv("PORT", "8000")
    
    print(f"\n🌍 Environment: {env}")
    print(f"📡 Port: {port}")
    print(f"🔒 HTTPS: {'Enabled' if os.getenv('RENDER') else 'Disabled (Local)'}")
    
    print(f"\n🌐 CORS Origins ({len(ALLOWED_ORIGINS)} domains):")
    for idx, origin in enumerate(ALLOWED_ORIGINS, 1):
        print(f"   {idx}. {origin}")
    
    print("\n📋 Registered Routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(sorted(route.methods))
            print(f"  {methods:30} → {route.path}")
    
    print("\n✅ Server is ready!")
    if not os.getenv("RENDER"):
        print("📖 API Docs: http://localhost:8000/docs")
        print("🔗 API Base: http://localhost:8000/api")
    else:
        print("📖 API Docs: https://api.thepureanddesi.com/docs")
        print("🔗 API Base: https://api.thepureanddesi.com/api")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    reload = not bool(os.getenv("RENDER"))  # Reload only in development
    
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        # ✅ Important for Render
        proxy_headers=True,
        forwarded_allow_ips="*"
    )