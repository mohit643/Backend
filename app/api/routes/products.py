# backend/app/api/routes/products.py
from fastapi import APIRouter, HTTPException
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
        "price": 399.0,
        "mrp": 499.0,
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
        "name": "Pure Groundnut Oil (Kachi Ghani)",
        "slug": "groundnut-oil",
        "category": "Groundnut Oil",
        "price": 349.0,
        "mrp": 449.0,
        "discount": 22,
        "size": "1",
        "unit": "Liter",
        "image": "/images/products/groundnut-oil.jpg",
        "description": "Traditional cold-pressed groundnut oil with rich aroma.",
        "inStock": True,
        "rating": 4.9,
        "reviews": 312
    },
    {
        "id": 4,
        "name": "Pure Sesame Oil (Kachi Ghani)",
        "slug": "sesame-oil",
        "category": "Sesame Oil",
        "price": 429.0,
        "mrp": 549.0,
        "discount": 22,
        "size": "500",
        "unit": "ml",
        "image": "/images/products/sesame-oil.jpg",
        "description": "Premium cold-pressed sesame oil with nutty flavor.",
        "inStock": True,
        "rating": 4.6,
        "reviews": 156
    },
    {
        "id": 5,
        "name": "Virgin Coconut Oil (Cold-Pressed)",
        "slug": "coconut-oil",
        "category": "Coconut Oil",
        "price": 389.0,
        "mrp": 489.0,
        "discount": 20,
        "size": "500",
        "unit": "ml",
        "image": "/images/products/coconut-oil.jpg",
        "description": "Extra virgin coconut oil extracted from fresh coconuts.",
        "inStock": True,
        "rating": 4.8,
        "reviews": 278
    }
]

@router.get("/", response_model=List[Product])
async def get_all_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False
):
    """
    Get all products with optional filters
    """
    try:
        filtered = PRODUCTS.copy()
        
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
        
        print(f"📦 Returning {len(filtered)} products")
        return filtered
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{slug}", response_model=Product)
async def get_product_by_slug(slug: str):
    """
    Get single product by slug
    """
    try:
        product = next((p for p in PRODUCTS if p["slug"] == slug), None)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        print(f"📦 Returning product: {product['name']}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_products_by_category(category: str):
    """
    Get products by category
    """
    try:
        products = [p for p in PRODUCTS if p["category"].lower() == category.lower()]
        
        print(f"📦 Found {len(products)} products in {category}")
        return {
            "category": category,
            "count": len(products),
            "products": products
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{query}")
async def search_products(query: str):
    """
    Search products
    """
    try:
        query_lower = query.lower()
        results = [
            p for p in PRODUCTS 
            if query_lower in p["name"].lower() or query_lower in p["description"].lower()
        ]
        
        print(f"🔍 Found {len(results)} results for '{query}'")
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))