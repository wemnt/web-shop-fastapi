from httpx import AsyncClient

from models.user import UserRole
from tests.typedefs import AuthHeaders, CreateOrder, CreateProduct, CreateUser


async def test_user_cannot_cancel_foreign_order(
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

    response = await client.post(
        f"/api/v1/orders/{order['id']}/cancel", headers=auth_headers(bob)
    )

    assert response.status_code == 404


async def test_cart_is_private(
    client: AsyncClient,
    create_user: CreateUser,
    create_product: CreateProduct,
    auth_headers: AuthHeaders,
) -> None:
    alice = await create_user(email="alice@test.com")
    bob = await create_user(email="bob@test.com")
    product = await create_product()

    response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers(alice),
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1

    response = await client.get("/api/v1/cart", headers=auth_headers(bob))

    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_blocked_user_gets_403(
    client: AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    admin = await create_user(email="admin@test.com", role=UserRole.ADMIN)
    alice = await create_user(email="alice@test.com")

    response = await client.post(
        f"/api/v1/admin/users/{alice.id}/block", headers=auth_headers(admin)
    )
    assert response.status_code == 200

    response = await client.get("/api/v1/users/me", headers=auth_headers(alice))
    assert response.status_code == 403


async def test_admin_cannot_block_self(
    client: AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    admin = await create_user(email="admin@test.com", role=UserRole.ADMIN)

    response = await client.post(
        f"/api/v1/admin/users/{admin.id}/block", headers=auth_headers(admin)
    )

    assert response.status_code == 400


async def test_login_rate_limit(client: AsyncClient) -> None:
    form = {"username": "nobody@test.com", "password": "wrong-password"}

    for _ in range(5):
        response = await client.post("/api/v1/auth/login", data=form)
        assert response.status_code == 401

    response = await client.post("/api/v1/auth/login", data=form)
    assert response.status_code == 429
