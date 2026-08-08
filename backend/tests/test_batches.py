import threading
from unittest.mock import patch
import httpx


# happy path
def test_create_batch_success(client):
    response = client.post(
        "/batches",
        headers={
            "X-API-Key": "dev-secret-key",
            "Idempotency-Key": "test-create-001",
        },
        json={
            "sample_id": "SAMPLE-001",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sample_id"] == "SAMPLE-001"
    assert data["batch_type"] == "PCR"
    assert data["submitted_by"] == "lab-user-01"

    # Newly created batches must always enter the pipeline in
    # the initial "queued" state.
    assert data["status"] == "queued"


# validation failure
def test_create_batch_validation_failure(client):
    response = client.post(
        "/batches",
        headers={
            "X-API-Key": "dev-secret-key",
            "Idempotency-Key": "test-validation-001",
        },
        json={
            # sample_id is intentionally omitted.
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    assert response.status_code == 422

    data = response.json()

    # FastAPI/Pydantic should reject the request before our
    # create_batch() business logic is executed.
    assert "detail" in data


# invalid status transition
def test_invalid_status_transition(client):
    # First create a batch. Newly created batches start in "queued".
    create_response = client.post(
        "/batches",
        headers={
            "X-API-Key": "dev-secret-key",
            "Idempotency-Key": "test-invalid-transition-001",
        },
        json={
            "sample_id": "SAMPLE-002",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    # "queued -> completed" is intentionally invalid because a
    # batch must go through "processing" before it can complete.
    response = client.patch(
        f"/batches/{batch_id}/status",
        headers={
            "X-API-Key": "dev-secret-key",
        },
        json={
            "status": "completed",
        },
    )

    assert response.status_code == 409

    data = response.json()

    assert "Invalid status transition" in data["detail"]

    # The failed transition must not modify the batch's state.
    get_response = client.get(
        f"/batches/{batch_id}",
        headers={
            "X-API-Key": "dev-secret-key",
        },
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "queued"


# concurrent update
def test_concurrent_status_update(client):
    # Create a batch that both concurrent requests will attempt to update.
    create_response = client.post(
        "/batches",
        headers={
            "X-API-Key": "dev-secret-key",
            "Idempotency-Key": "test-concurrency-001",
        },
        json={
            "sample_id": "SAMPLE-003",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    results = []
    barrier = threading.Barrier(2)

    def update_status():
        # Wait until both threads are ready so they attempt the
        # state transition at approximately the same time.
        barrier.wait()

        response = client.patch(
            f"/batches/{batch_id}/status",
            headers={
                "X-API-Key": "dev-secret-key",
            },
            json={
                "status": "processing",
            },
        )

        results.append(response.status_code)

    thread_1 = threading.Thread(target=update_status)
    thread_2 = threading.Thread(target=update_status)

    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()

    # Exactly one request should successfully transition the batch.
    assert results.count(200) == 1

    # The other request must be rejected because the batch is no
    # longer in the "queued" state when its atomic UPDATE executes.
    assert results.count(409) == 1

    # Verify the final database state is consistent.
    get_response = client.get(
        f"/batches/{batch_id}",
        headers={
            "X-API-Key": "dev-secret-key",
        },
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "processing"


# authentication failure
def test_authentication_failure(client):
    response = client.get(
        "/batches/1",
        headers={
            "X-API-Key": "invalid-api-key",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid API key"


# idempotency test
def test_create_batch_is_idempotent(client):
    headers = {
        "X-API-Key": "dev-secret-key",
        "Idempotency-Key": "test-idempotency-001",
    }

    payload = {
        "sample_id": "SAMPLE-IDEMPOTENT-001",
        "batch_type": "PCR",
        "submitted_by": "lab-user-01",
    }

    # First request creates the batch.
    first_response = client.post(
        "/batches",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201

    first_batch = first_response.json()

    # Retry the exact same request with the same idempotency key.
    second_response = client.post(
        "/batches",
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 201

    second_batch = second_response.json()

    # The retry must return the original batch rather than creating
    # a second database record.
    assert second_batch["id"] == first_batch["id"]

    assert second_batch["sample_id"] == first_batch["sample_id"]
    assert second_batch["batch_type"] == first_batch["batch_type"]
    assert second_batch["submitted_by"] == first_batch["submitted_by"]


# filtering by status
def test_list_batches_with_status_filter(client):
    headers = {
        "X-API-Key": "dev-secret-key",
    }

    # Create two batches.
    first_response = client.post(
        "/batches",
        headers={
            **headers,
            "Idempotency-Key": "test-list-status-001",
        },
        json={
            "sample_id": "SAMPLE-LIST-001",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    second_response = client.post(
        "/batches",
        headers={
            **headers,
            "Idempotency-Key": "test-list-status-002",
        },
        json={
            "sample_id": "SAMPLE-LIST-002",
            "batch_type": "RNA",
            "submitted_by": "lab-user-02",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_batch_id = first_response.json()["id"]

    # Move the first batch from queued -> processing.
    status_response = client.patch(
        f"/batches/{first_batch_id}/status",
        headers=headers,
        json={
            "status": "processing",
        },
    )

    assert status_response.status_code == 200

    # Filter the list by status.
    response = client.get(
        "/batches",
        headers=headers,
        params={
            "status": "processing",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Every returned batch must match the requested status.
    assert all(batch["status"] == "processing" for batch in data["items"])

    # Our first batch should be present in the filtered result.
    assert any(batch["id"] == first_batch_id for batch in data["items"])


# filtering by batch type
def test_list_batches_with_type_filter(client):
    headers = {
        "X-API-Key": "dev-secret-key",
    }

    client.post(
        "/batches",
        headers={
            **headers,
            "Idempotency-Key": "test-list-type-001",
        },
        json={
            "sample_id": "SAMPLE-TYPE-001",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
        },
    )

    client.post(
        "/batches",
        headers={
            **headers,
            "Idempotency-Key": "test-list-type-002",
        },
        json={
            "sample_id": "SAMPLE-TYPE-002",
            "batch_type": "RNA",
            "submitted_by": "lab-user-02",
        },
    )

    response = client.get(
        "/batches",
        headers=headers,
        params={
            "type": "RNA",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert all(batch["batch_type"] == "RNA" for batch in data["items"])


# pagination test
def test_list_batches_pagination(client):
    headers = {
        "X-API-Key": "dev-secret-key",
    }

    # Create three batches.
    for index in range(3):
        response = client.post(
            "/batches",
            headers={
                **headers,
                "Idempotency-Key": f"test-pagination-{index}",
            },
            json={
                "sample_id": f"SAMPLE-PAGE-{index}",
                "batch_type": "PCR",
                "submitted_by": "lab-user-01",
            },
        )

        assert response.status_code == 201

    response = client.get(
        "/batches",
        headers=headers,
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


# webhook notification test
def test_notify_batch_success(client):
    headers = {
        "X-API-Key": "dev-secret-key",
        "Idempotency-Key": "test-notify-success-001",
    }

    # Use a public-looking HTTPS URL for the partner webhook.
    # The actual network request will be mocked below.
    webhook_url = "https://partner.example.com/webhook"

    create_response = client.post(
        "/batches",
        headers=headers,
        json={
            "sample_id": "SAMPLE-NOTIFY-001",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
            "partner_webhook": webhook_url,
        },
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    # Mock DNS resolution because the test must never perform real
    # external network operations.
    fake_address = (
        None,
        None,
        None,
        None,
        ("93.184.216.34", 443),
    )

    with (
        patch(
            "app.services.notify.socket.getaddrinfo",
            return_value=[fake_address],
        ),
        patch(
            "app.services.notify.httpx.post",
        ) as mock_post,
    ):
        # Simulate a successful partner response.
        mock_post.return_value.raise_for_status.return_value = None

        response = client.post(
            f"/batches/{batch_id}/notify",
            headers={
                "X-API-Key": "dev-secret-key",
            },
        )

    assert response.status_code == 202

    data = response.json()

    assert data["batch_id"] == batch_id
    assert data["message"] == "Batch notification sent successfully"

    # Verify that our service actually attempted to call the
    # configured partner webhook.
    mock_post.assert_called_once_with(
        webhook_url,
        json={
            "batch_id": batch_id,
            "sample_id": "SAMPLE-NOTIFY-001",
            "batch_type": "PCR",
            "status": "queued",
            "result": None,
        },
        timeout=5,
    )


# webhook notification failure with retries
def test_notify_batch_retries_on_webhook_failure(client):
    headers = {
        "X-API-Key": "dev-secret-key",
        "Idempotency-Key": "test-notify-retry-001",
    }

    webhook_url = "https://partner.example.com/webhook"

    create_response = client.post(
        "/batches",
        headers=headers,
        json={
            "sample_id": "SAMPLE-NOTIFY-002",
            "batch_type": "PCR",
            "submitted_by": "lab-user-01",
            "partner_webhook": webhook_url,
        },
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    fake_address = (
        None,
        None,
        None,
        None,
        ("93.184.216.34", 443),
    )

    with (
        patch(
            "app.services.notify.socket.getaddrinfo",
            return_value=[fake_address],
        ),
        patch(
            "app.services.notify.httpx.post",
        ) as mock_post,
        patch(
            "app.services.notify.time.sleep",
        ) as mock_sleep,
    ):
        # Simulate the partner webhook failing on every attempt.
        mock_post.side_effect = httpx.ConnectError("Partner unavailable")

        response = client.post(
            f"/batches/{batch_id}/notify",
            headers={
                "X-API-Key": "dev-secret-key",
            },
        )

    assert response.status_code == 502

    data = response.json()

    assert data["detail"] == "Webhook notification failed after all retries"

    # MAX_RETRIES is 3, so the implementation makes 4 total attempts.
    assert mock_post.call_count == 4

    # Exponential backoff should be:
    #
    # attempt 1 -> sleep 1 second
    # attempt 2 -> sleep 2 seconds
    # attempt 3 -> sleep 4 seconds
    #
    # No sleep occurs after the final attempt.
    assert [call.args[0] for call in mock_sleep.call_args_list] == [
        1,
        2,
        4,
    ]
