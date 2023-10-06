import unittest.mock

from redis import ConnectionError


@unittest.mock.patch('docker_redis_cicd.app.redis')
def test_should_call_redis_incr(mock_redis, http_client):
    mock_redis.return_value.incr.return_value = 1

    response = http_client.get('/')

    assert response.status_code == 200
    assert response.text == 'This page has been seen 1 times.'
    mock_redis.return_value.incr.assert_called_once_with('page_views')


@unittest.mock.patch("docker_redis_cicd.app.redis")
def test_should_handle_redis_connection_error(mock_redis, http_client):
    # Given
    mock_redis.return_value.incr.side_effect = ConnectionError

    # When
    response = http_client.get("/")

    # Then
    assert response.status_code == 500
    assert response.text == "Sorry, something went wrong \N{pensive face}"
