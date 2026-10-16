from httpx import AsyncClient

from tests.typedefs import AuthHeaders, CreateUser


async def test_register_returns_201(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={"email": "kizaru@gmail.com", "name": "oleg", "password": "12341234"},
    )
    assert response.status_code == 201


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:

    payload = {"email": "kizaru@gmail.com", "name": "oleg", "password": "12341234"}

    response = await client.post(
        "/api/v1/users",
        json=payload,
    )

    assert response.status_code == 201

    response = await client.post(
        "/api/v1/users",
        json=payload,
    )
    assert response.status_code == 409


async def test_get_me_returns_current_user(
    client: AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    alice = await create_user(email="alice@test.com")
    response = await client.get("/api/v1/users/me", headers=auth_headers(alice))
    assert response.status_code == 200
    assert response.json()["email"] == alice.email


async def test_get_me_with_no_headers_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
