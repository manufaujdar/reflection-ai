def create_user(client, consent=True):
    response = client.post("/v1/users", json={"external_id": "user-1", "consent": consent})
    assert response.status_code == 201
    return response.json()


def test_local_research_console_is_explicitly_synthetic(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Reflection AI research console" in response.text
    assert "Authentication and tenant isolation are not implemented" in response.text


def test_capabilities_make_privacy_invariants_discoverable(client):
    response = client.get("/v1/capabilities")
    assert response.status_code == 200
    assert response.json() == {
        "provider_agnostic": True,
        "consent_required_for_storage": True,
        "training_consent_required": True,
        "deletion_supported": True,
        "evidence_linked_memory": True,
        "production_ready": False,
    }


def test_generate_and_capture_event(client):
    user = create_user(client)
    response = client.post(f"/v1/users/{user['id']}/generate", json={"prompt": "Hello"})
    assert response.status_code == 200
    assert response.json()["text"] == "[personalized mock] Hello"
    assert response.json()["event_id"]


def test_event_requires_consent(client):
    user = create_user(client, consent=False)
    response = client.post(
        f"/v1/users/{user['id']}/events",
        json={"kind": "preference", "attributes": {"preferred_style": "concise"}},
    )
    assert response.status_code == 403


def test_refresh_learns_explicit_style(client):
    user = create_user(client)
    client.post(
        f"/v1/users/{user['id']}/events",
        json={"kind": "preference", "attributes": {"preferred_style": "concise"}},
    )
    response = client.post(f"/v1/users/{user['id']}/profile/refresh")
    assert response.json()["preferences"]["preferred_style"] == "concise"


def test_subject_identity_is_scoped_by_application(client):
    cdss = client.post(
        "/v1/subjects/resolve",
        json={"application_id": "cdss", "external_id": "shared-user", "consent": True},
    ).json()
    masterllm = client.post(
        "/v1/subjects/resolve",
        json={"application_id": "masterllm", "external_id": "shared-user", "consent": True},
    ).json()
    assert cdss["id"] != masterllm["id"]


def test_resolving_subject_updates_consent(client):
    initial = client.post(
        "/v1/subjects/resolve",
        json={"application_id": "cdss", "external_id": "consent-user"},
    ).json()
    updated = client.post(
        "/v1/subjects/resolve",
        json={
            "application_id": "cdss",
            "external_id": "consent-user",
            "consent": True,
            "training_consent": True,
        },
    ).json()
    assert initial["id"] == updated["id"]
    assert updated["consent"] is True
    assert updated["training_consent"] is True


def test_context_maps_existing_chat_fields(client):
    user = client.post(
        "/v1/subjects/resolve",
        json={"application_id": "cdss", "external_id": "doctor-1", "consent": True},
    ).json()
    client.post(
        f"/v1/users/{user['id']}/events",
        json={"kind": "preference", "attributes": {"preferred_style": "concise"}},
    )
    client.post(f"/v1/users/{user['id']}/profile/refresh")
    response = client.post(
        "/v1/context",
        json={
            "application_id": "cdss",
            "external_user_id": "doctor-1",
            "session_id": "session-1",
            "base_system_prompt": "Clinical policy stays first.",
            "host_personalization": {"profession": "doctor"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["personalization_applied"] is True
    assert payload["prompt"]["system_prompt"].startswith("Clinical policy stays first.")
    assert "concise" in payload["prompt"]["system_prompt"]


def test_protected_clinical_mode_never_modifies_prompt(client):
    client.post(
        "/v1/subjects/resolve",
        json={"application_id": "cdss", "external_id": "doctor-2", "consent": True},
    )
    response = client.post(
        "/v1/context",
        json={
            "application_id": "cdss",
            "external_user_id": "doctor-2",
            "base_system_prompt": "Immutable deep-analysis policy.",
            "safety": {"mode": "deep_analysis"},
        },
    )
    payload = response.json()
    assert payload["personalization_applied"] is False
    assert payload["prompt"]["system_prompt"] == "Immutable deep-analysis policy."
    assert payload["personalization_reason"] == "protected_mode:deep_analysis"


def test_event_idempotency(client):
    user = create_user(client)
    event = {
        "kind": "interaction",
        "idempotency_key": "session-1:message-1:complete",
        "session_id": "session-1",
        "message_id": "message-1",
    }
    first = client.post(f"/v1/users/{user['id']}/events", json=event).json()
    second = client.post(f"/v1/users/{user['id']}/events", json=event).json()
    assert first["id"] == second["id"]
    assert first["duplicate"] is False
    assert second["duplicate"] is True
