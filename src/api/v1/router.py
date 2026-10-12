from fastapi import APIRouter

from .endpoints import auth, cart, products, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(auth.router)
api_router.include_router(cart.router)
