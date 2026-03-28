import pytest
from httpx import AsyncClient

# ─── helpers ──────────────────────────────────────────────────────────────────

async def register(client: AsyncClient, username: str, email: str, password: str = "password123"):
    return await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )

async def login(client: AsyncClient, username: str, password: str = "password123"):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )

# ─── registration ─────────────────────────────────────────────────────────────

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
    reg_response = await register(client, "meuser", "meuser@example.com")
    token = reg_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["email"] == "meuser@example.com"
    assert "id" in data


# ─── validation ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient):
    """Пароль меньше 6 символов — должен вернуть 422."""
    response = await register(client, "shortpass", "shortpass@example.com", password="12345")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("6" in str(e) or "characters" in str(e).lower() for e in detail)


@pytest.mark.asyncio
async def test_register_password_min_length_ok(client: AsyncClient):
    """Ровно 6 символов — должен пройти."""
    response = await register(client, "pass6user", "pass6@example.com", password="abc123")
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Невалидный email — должен вернуть 422."""
    response = await register(client, "bademail", "notanemail")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Дублирующийся email — должен вернуть 400."""
    await register(client, "emailuser1", "shared@example.com")
    response = await register(client, "emailuser2", "shared@example.com")
    assert response.status_code == 400


# ─── login ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Несуществующий пользователь — должен вернуть 401."""
    response = await login(client, "ghost_user_xyz")
    assert response.status_code == 401


# ─── token refresh ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Refresh token возвращает новую пару токенов."""
    reg = await register(client, "refreshuser", "refreshuser@example.com")
    refresh_token = reg.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Невалидный refresh token — должен вернуть 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


# ─── full flow ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_register_login_me_flow(client: AsyncClient):
    """Полный цикл: регистрация → логин → /me."""
    username = "flowuser"
    email = "flow@example.com"
    password = "mypassword"

    # Регистрация
    reg = await register(client, username, email, password)
    assert reg.status_code == 200

    # Логин
    log = await login(client, username, password)
    assert log.status_code == 200
    token = log.json()["access_token"]

    # /me с токеном от логина
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == username
    assert me.json()["email"] == email
