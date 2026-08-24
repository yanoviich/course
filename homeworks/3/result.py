import requests

BASE_URL = "https://jsonplaceholder.typicode.com"


def test_posts_endpoint_returns_200():
    response = requests.get(f"{BASE_URL}/posts")
    assert response.status_code == 200


def test_posts_with_invalid_data_returns_400():
    data = {"title": "", "body": "", "userId": "invalid"}
    response = requests.post(f"{BASE_URL}/posts", json=data)
    assert response.status_code == 400


def test_get_nonexistent_post_returns_404():
    response = requests.get(f"{BASE_URL}/posts/{99999}")
    assert response.status_code == 404