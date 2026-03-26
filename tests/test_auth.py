import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dupuser1@example.com",
            "password": "securepassword123",
        },
    )
    # Second registration with same username
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dupuser2@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "securepassword123",
        },
    )
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "loginuser",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpassuser",
            "email": "wrongpassuser@example.com",
            "password": "securepassword123",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "wrongpassuser",
            "password": "wrongpassword999",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    # Register and get token
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "meuser",
            "email": "meuser@example.com",
            "password": "securepassword123",
        },
    )
    token = reg_response.json()["access_token"]

    # Use token to get /me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
