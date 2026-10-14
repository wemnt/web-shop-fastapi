from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from api.deps import ProductServiceDep, require_admin
from models.product import Product
from schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_product_endpoint(
    data: ProductCreate, products: ProductServiceDep
) -> Product:
    return await products.create(data=data)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product_endpoint(
    product_id: UUID, products: ProductServiceDep
) -> Product:
    return await products.get(product_id=product_id)


@router.get("", response_model=list[ProductRead])
async def get_products(
    products: ProductServiceDep,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    page: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Product]:
    return await products.list_products(page=page, size=size)


@router.patch(
    "/{product_id}", response_model=ProductRead, dependencies=[Depends(require_admin)]
)
async def update_product_endpoint(
    product_id: UUID, data: ProductUpdate, products: ProductServiceDep
) -> Product:
    return await products.update(product_id=product_id, data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_product_endpoint(
    product_id: UUID, products: ProductServiceDep
) -> None:
    await products.delete(product_id=product_id)
