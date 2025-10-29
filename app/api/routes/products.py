# backend/app/api/routes/products.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class Product(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    price: float
    mrp: float
    discount: int
    size: str
    unit: str
    image: str
    description: str
    inStock: bool
    rating: float
    reviews: int

# Sample products data
PRODUCTS = [
    {
        "id": 1,
        "name": "Premium Black Mustard Oil (Kachi Ghani)",
        "slug": "black-mustard-oil",
        "category": "Mustard Oil",
        "price": 399,
        "mrp":  499,
        "discount": 20,
        "size": "1",
        "unit": "Liter",
        "image": "/images/products/black-mustard-oil.jpg",
        "description": "Pure cold-pressed black mustard oil extracted using traditional wooden Ghani method.",
        "inStock": True,
        "rating": 4.8,
        "reviews": 234
    },
    {
        "id": 2,
        "name": "Yellow Mustard Oil (Kachi Ghani)",
        "slug": "yellow-mustard-oil",
        "category": "Mustard Oil",
        "price": 379.0,
        "mrp": 479.0,
        "discount": 21,
        "size": "1",
        "unit": "Liter",
        "image": "/images/products/yellow-mustard-oil.jpg",
        "description": "Cold-pressed yellow mustard oil with mild flavor.",
        "inStock": True,
        "rating": 4.7,
        "reviews": 189
    },
    {
        "id": 3,
        "name": "Groundnut Oil (Cold Pressed)",
        "slug": "groundnut-oil",
        "category": "Groundnut Oil",
        "price": 180.0,
        "mrp": 280.0,
        "discount": 36,
        "size": "1",
        "unit": "Liter",
        "image": "/images/products/groundnut-oil.jpg",
        "description": "Premium cold-pressed groundnut oil, ideal for cooking.",
        "inStock": True,
        "rating": 4.6,
        "reviews": 156
    },
    {
        "id": 4,
        "name": "Sesame Oil (Til Oil)",
        "slug": "sesame-oil",
        "category": "Sesame Oil",
        "price": 220.0,
        "mrp": 320.0,
        "discount": 31,
        "size": "1",
        "unit": "Liter",
        "image": "/images/products/sesame-oil.jpg",
        "description": "Pure sesame oil, rich in nutrients and flavor.",
        "inStock": True,
        "rating": 4.9,
        "reviews": 298
    },
    {
        "id": 5,
        "name": "Coconut Oil (Virgin)",
        "slug": "coconut-oil",
        "category": "Coconut Oil",
        "price": 250.0,
        "mrp": 350.0,
        "discount": 29,
        "size": "500",
        "unit": "ML",
        "image": "/images/products/coconut-oil.jpg",
        "description": "Extra virgin coconut oil for cooking and hair care.",
        "inStock": True,
        "rating": 4.8,
        "reviews": 412
    },
]

# ✅ Handle both with and without trailing slash
@router.get("", response_model=List[Product])
@router.get("/", response_model=List[Product])
async def get_all_products(
    email: Optional[str] = Query(None, description="User email for personalized results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    in_stock_only: bool = Query(False, description="Show only in-stock products")
):
    """
    Get all products with optional filters
    
    Query Parameters:
    - email: User email (optional, for analytics)
    - category: Filter by product category
    - search: Search text in name/description
    - min_price: Minimum price
    - max_price: Maximum price
    - in_stock_only: Show only available products
    """
    try:
        filtered = PRODUCTS.copy()
        
        # Email for analytics (optional)
        if email:
            print(f"📧 Request from: {email}")
        
        # Category filter
        if category:
            filtered = [p for p in filtered if p["category"].lower() == category.lower()]
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in filtered 
                if search_lower in p["name"].lower() or search_lower in p["description"].lower()
            ]
        
        # Price range filter
        if min_price is not None:
            filtered = [p for p in filtered if p["price"] >= min_price]
        if max_price is not None:
            filtered = [p for p in filtered if p["price"] <= max_price]
        
        # Stock filter
        if in_stock_only:
            filtered = [p for p in filtered if p["inStock"]]
        
        print(f"📦 Returning {len(filtered)} products (from total {len(PRODUCTS)})")
        return filtered
        
    except Exception as e:
        print(f"❌ Error in get_all_products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{slug}", response_model=Product)
async def get_product_by_slug(slug: str):
    """
    Get single product by slug
    
    Path Parameters:
    - slug: Product URL slug (e.g., 'black-mustard-oil')
    """
    try:
        product = next((p for p in PRODUCTS if p["slug"] == slug), None)
        
        if not product:
            raise HTTPException(
                status_code=404, 
                detail=f"Product with slug '{slug}' not found"
            )
        
        print(f"📦 Returning product: {product['name']}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_product_by_slug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/category/{category}")
async def get_products_by_category(category: str):
    """
    Get products by category
    
    Path Parameters:
    - category: Product category name
    """
    try:
        products = [p for p in PRODUCTS if p["category"].lower() == category.lower()]
        
        print(f"📦 Found {len(products)} products in category '{category}'")
        return {
            "status": "success",
            "category": category,
            "count": len(products),
            "products": products
        }
        
    except Exception as e:
        print(f"❌ Error in get_products_by_category: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/search/{query}")
async def search_products(query: str):
    """
    Search products by query
    
    Path Parameters:
    - query: Search text
    """
    try:
        query_lower = query.lower()
        results = [
            p for p in PRODUCTS 
            if query_lower in p["name"].lower() or 
               query_lower in p["description"].lower() or
               query_lower in p["category"].lower()
        ]
        
        print(f"🔍 Found {len(results)} results for query '{query}'")
        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Error in search_products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ✅ Categories endpoint
@router.get("/meta/categories")
async def get_categories():
    """Get all unique product categories"""
    try:
        categories = list(set(p["category"] for p in PRODUCTS))
        return {
            "status": "success",
            "count": len(categories),
            "categories": categories
        }
    except Exception as e:
        print(f"❌ Error in get_categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Stats endpoint
@router.get("/meta/stats")
async def get_product_stats():
    """Get product statistics"""
    try:
        in_stock = sum(1 for p in PRODUCTS if p["inStock"])
        categories = len(set(p["category"] for p in PRODUCTS))
        avg_price = sum(p["price"] for p in PRODUCTS) / len(PRODUCTS)
        
        return {
            "status": "success",
            "stats": {
                "total_products": len(PRODUCTS),
                "in_stock": in_stock,
                "out_of_stock": len(PRODUCTS) - in_stock,
                "categories": categories,
                "average_price": round(avg_price, 2)
            }
        }
    except Exception as e:
        print(f"❌ Error in get_product_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))