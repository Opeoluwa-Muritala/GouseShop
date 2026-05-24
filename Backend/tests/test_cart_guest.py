def test_guest_cart_requires_session(client):
    response = client.get("/api/v1/cart/")
    assert response.status_code == 400
