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
    assert data["status"] == "queued"
