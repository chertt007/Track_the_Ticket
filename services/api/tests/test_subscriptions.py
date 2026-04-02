import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint should return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_subscription(client: AsyncClient):
    """POST /subscriptions should create a pending subscription."""
    response = await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/MOW1201LED1", "check_frequency": 3},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["is_active"] is True
    assert data["check_frequency"] == 3
    assert "aviasales" in data["source_url"]


@pytest.mark.asyncio
async def test_create_subscription_invalid_url(client: AsyncClient):
    """POST /subscriptions with invalid URL should return 422."""
    response = await client.post(
        "/subscriptions",
        json={"source_url": "not-a-url"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_subscriptions_empty(client: AsyncClient):
    """GET /subscriptions should return empty list when no subscriptions."""
    response = await client.get("/subscriptions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_subscriptions(client: AsyncClient):
    """GET /subscriptions should return all active subscriptions."""
    # Create two subscriptions
    await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/MOW1201LED1"},
    )
    await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/LED0503MOW1"},
    )

    response = await client.get("/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_subscription_by_id(client: AsyncClient):
    """GET /subscriptions/{id} should return a single subscription."""
    create_response = await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/MOW1201LED1"},
    )
    subscription_id = create_response.json()["id"]

    response = await client.get(f"/subscriptions/{subscription_id}")
    assert response.status_code == 200
    assert response.json()["id"] == subscription_id


@pytest.mark.asyncio
async def test_get_subscription_not_found(client: AsyncClient):
    """GET /subscriptions/999 should return 404."""
    response = await client.get("/subscriptions/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_subscription(client: AsyncClient):
    """DELETE /subscriptions/{id} should soft-delete (is_active=False)."""
    create_response = await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/MOW1201LED1"},
    )
    subscription_id = create_response.json()["id"]

    delete_response = await client.delete(f"/subscriptions/{subscription_id}")
    assert delete_response.status_code == 204

    # Should no longer appear in the list
    list_response = await client.get("/subscriptions")
    ids = [s["id"] for s in list_response.json()]
    assert subscription_id not in ids


@pytest.mark.asyncio
async def test_delete_subscription_not_found(client: AsyncClient):
    """DELETE /subscriptions/999 should return 404."""
    response = await client.delete("/subscriptions/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_price_history_empty(client: AsyncClient):
    """GET /subscriptions/{id}/prices should return empty list."""
    create_response = await client.post(
        "/subscriptions",
        json={"source_url": "https://www.aviasales.ru/search/MOW1201LED1"},
    )
    subscription_id = create_response.json()["id"]

    response = await client.get(f"/subscriptions/{subscription_id}/prices")
    assert response.status_code == 200
    assert response.json() == []
