def test_root_redirects_to_admin(backoffice_client):
    response = backoffice_client.get("/")
    assert response.status_code == 302
    assert response.url == "/admin/"
