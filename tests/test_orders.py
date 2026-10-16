from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.typedefs import AuthHeaders, CreateOrder, CreateProduct, CreateUser


async def test_customer_cannot_access_admin(
    client: AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    alice = await create_user(email="alice@test.com")

    response = await client.get("/api/v1/admin/orders", headers=auth_headers(alice))

    assert response.status_code == 403


async def test_user_cannot_get_foreign_order(
    client: AsyncClient,
    create_user: CreateUser,
    create_product: CreateProduct,
    create_order: CreateOrder,
    auth_headers: AuthHeaders,
) -> None:
    alice = await create_user(email="alice@test.com")
    bob = await create_user(email="bob@test.com")
    product = await create_product()
    order = await create_order(alice, product)

    response = await client.get(
        f"/api/v1/orders/{order['id']}", headers=auth_headers(bob)
    )

    assert response.status_code == 404


async def test_order_decreases_stock(
    session: AsyncSession,
    create_user: CreateUser,
    create_product: CreateProduct,
    create_order: CreateOrder,
) -> None:
    alice = await create_user(email="alice@test.com")
    product = await create_product(stock=5)

    await create_order(alice, product, quantity=2)

    await session.refresh(product)
    assert product.stock == 3
