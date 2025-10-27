# backend/run.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Pure & Desi API",
    description="Premium Cold-Pressed Oil E-commerce Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",
        # "http://localhost:5173",
        # "http://127.0.0.1:3000",
        # "http://127.0.0.1:5173",
          "https://api.thepureanddesi.com",
        "https://thepureanddesi.com",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api.routes import products, orders, contact, delivery, payments, whatsapp, admin
from app.api.routes import auth   # ✅ Use existing auth

# Include Routers
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(delivery.router, prefix="/api")
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])

# ✅ Auth & Admin
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pure & Desi API",
        "status": "running",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }

@app.get("/api")
async def api_info():
    return {
        "message": "Pure & Desi API Endpoints",
        "endpoints": {
            "orders": "/api/orders",
            "products": "/api/products",
            "delivery": "/api/delivery",
            "payments": "/api/payments",
            "whatsapp": "/api/whatsapp",
            "contact": "/api/contact",
            "auth": "/api/auth",
            "admin": "/api/admin"
        }
    }

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 Pure & Desi API Starting...")
    print("=" * 60)
    
    print("\n📋 Registered Routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods:8} {route.path}")
    
    print("\n✅ Server is ready!")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔗 API Base: http://localhost:8000/api")
    print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )