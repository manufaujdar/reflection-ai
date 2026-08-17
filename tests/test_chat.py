from reflection_ai.chat.questions import QUESTIONS


def create_session(client, external_user_id="chat-user", training_consent=False):
    response = client.post(
        "/v1/chat/sessions",
        json={
            "external_user_id": external_user_id,
            "consent": True,
            "training_consent": training_consent,
        },
    )
    assert response.status_code == 201
    return response.json()


def complete_onboarding(client, session):
    answers = {
        "display_name": "M",
        "response_depth": "Concise",
        "tone": "Warm",
        "format": "Bullets",
        "examples": "When helpful",
        "current_goal": "Build reliable software",
        "boundaries": "Do not overstate certainty",
    }
    state = {
        "progress": session["onboarding_index"],
        "total": session["onboarding_total"],
        "next_question": session["next_question"],
    }
    learned = []
    while state["next_question"]:
        question_id = state["next_question"]["id"]
        response = client.post(
            f"/v1/chat/sessions/{session['id']}/onboarding",
            json={"question_id": question_id, "answer": answers[question_id]},
        )
        assert response.status_code == 200
        state = response.json()
        learned.append(state["learned_memory_id"])
    assert state["complete"] is True
    return learned


def test_chat_requires_consent_and_onboarding(client):
    denied = client.post(
        "/v1/chat/sessions", json={"external_user_id": "no-consent", "consent": False}
    )
    assert denied.status_code == 403

    session = create_session(client)
    premature = client.post(
        f"/v1/chat/sessions/{session['id']}/messages", json={"message": "Hello"}
    )
    assert premature.status_code == 409
    assert session["onboarding_total"] == len(QUESTIONS)


def test_onboarding_creates_explicit_evidence_backed_memory(client):
    session = create_session(client)
    memory_ids = complete_onboarding(client, session)
    assert all(memory_ids)

    inspector = client.get(
        f"/v1/chat/sessions/{session['id']}/personalization"
    ).json()
    assert len(inspector["memories"]) == len(QUESTIONS)
    assert all(item["explicit"] for item in inspector["memories"])
    assert all(item["evidence_ids"] for item in inspector["memories"])
    assert any(item["content"] == "Prefer Concise responses" for item in inspector["memories"])


def test_adaptive_chat_persists_messages_and_learns_safe_style(client):
    session = create_session(client)
    complete_onboarding(client, session)
    last_reply = None
    for text in ("First short question?", "Second short question?", "Third short question?"):
        response = client.post(
            f"/v1/chat/sessions/{session['id']}/messages", json={"message": text}
        )
        assert response.status_code == 200
        last_reply = response.json()

    assert last_reply["assistant_message"]["content"].startswith("[personalized mock]")
    assert last_reply["personalization"]["style_samples"] == 3
    assert last_reply["personalization"]["style_instructions"]
    assert last_reply["agent_run_id"]

    history = client.get(f"/v1/chat/sessions/{session['id']}/messages").json()
    assert [message["role"] for message in history] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    inspector = client.get(
        f"/v1/chat/sessions/{session['id']}/personalization"
    ).json()
    assert inspector["style"]["sample_count"] == 3
    assert inspector["style"]["safe_scope"] == "observable writing mechanics only"
    assert inspector["recent_agent_runs"][0]["trace"]["stages"][-1] == "response-agent"
    assert inspector["recent_agent_runs"][0]["trace"]["history_message_count"] == 4
    assert inspector["learning"]["immediate_mode"].startswith("evidence-backed")
    assert inspector["learning"]["reference_slm"] == "optional_experiment_not_routed"


def test_chat_redacts_secrets_before_storage_and_generation(client):
    session = create_session(client)
    complete_onboarding(client, session)
    response = client.post(
        f"/v1/chat/sessions/{session['id']}/messages",
        json={"message": "My api_key=super-secret should not be stored"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "super-secret" not in body["user_message"]["content"]
    assert body["user_message"]["redacted"] is True
    assert "super-secret" not in body["assistant_message"]["content"]


def test_explicit_correction_becomes_provenance_linked_memory(client):
    session = create_session(client)
    complete_onboarding(client, session)
    reply = client.post(
        f"/v1/chat/sessions/{session['id']}/messages",
        json={"message": "Explain the design"},
    ).json()
    feedback = client.post(
        f"/v1/chat/messages/{reply['assistant_message']['id']}/feedback",
        json={"rating": -1, "correction": "Lead with the outcome before technical details"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["learned"] is True
    assert feedback.json()["memory_id"]

    memories = client.get(
        f"/v1/chat/sessions/{session['id']}/personalization"
    ).json()["memories"]
    correction = next(item for item in memories if item["id"] == feedback.json()["memory_id"])
    assert correction["explicit"] is True
    assert correction["evidence_ids"]


def test_helpful_feedback_updates_training_readiness_without_training_inline(client):
    session = create_session(client, "training-ready", training_consent=True)
    complete_onboarding(client, session)
    reply = client.post(
        f"/v1/chat/sessions/{session['id']}/messages",
        json={"message": "Give me a concise project update"},
    ).json()
    feedback = client.post(
        f"/v1/chat/messages/{reply['assistant_message']['id']}/feedback",
        json={"rating": 1},
    )
    assert feedback.status_code == 200
    learning = client.get(
        f"/v1/chat/sessions/{session['id']}/personalization"
    ).json()["learning"]
    assert learning["training_consent"] is True
    assert learning["positive_examples"] == 1
    assert learning["dataset_ready"] is False
    assert learning["reference_slm"] == "optional_experiment_not_routed"


def test_chat_subjects_are_isolated_and_deletion_covers_chat_layers(client):
    first = create_session(client, "isolated-one")
    second = create_session(client, "isolated-two")
    complete_onboarding(client, first)
    complete_onboarding(client, second)

    first_memories = client.get(
        f"/v1/chat/sessions/{first['id']}/personalization"
    ).json()["memories"]
    second_memories = client.get(
        f"/v1/chat/sessions/{second['id']}/personalization"
    ).json()["memories"]
    assert {item["id"] for item in first_memories}.isdisjoint(
        {item["id"] for item in second_memories}
    )

    deleted = client.delete(f"/v1/users/{first['user_id']}")
    assert deleted.status_code == 204
    assert client.get(f"/v1/chat/sessions/{first['id']}").status_code == 404
    assert client.get(f"/v1/chat/sessions/{second['id']}").status_code == 200


def test_chat_learning_can_pause_and_memory_revoke_is_session_scoped(client):
    first = create_session(client, "control-one")
    second = create_session(client, "control-two")
    first_memories = complete_onboarding(client, first)
    complete_onboarding(client, second)

    paused = client.patch(
        f"/v1/chat/sessions/{first['id']}/learning", json={"enabled": False}
    )
    assert paused.status_code == 200
    assert paused.json() == {"enabled": False}
    before = client.get(
        f"/v1/chat/sessions/{first['id']}/personalization"
    ).json()["style"]["sample_count"]
    assert client.post(
        f"/v1/chat/sessions/{first['id']}/messages", json={"message": "Do not learn this"}
    ).status_code == 200
    inspector = client.get(
        f"/v1/chat/sessions/{first['id']}/personalization"
    ).json()
    assert inspector["style"]["sample_count"] == before
    assert inspector["learning"]["enabled"] is False

    foreign = client.delete(
        f"/v1/chat/sessions/{second['id']}/memories/{first_memories[0]}"
    )
    assert foreign.status_code == 404
    revoked = client.delete(
        f"/v1/chat/sessions/{first['id']}/memories/{first_memories[0]}"
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"


def test_chat_frontend_and_capabilities_are_available(client):
    page = client.get("/chat")
    assert page.status_code == 200
    assert "The more you talk, the more Reflection works like you do" in page.text
    assert "It adapts as you talk" in page.text
    assert "evaluation-gated model training" in page.text
    assert "no authentication or encryption" in page.text
    assert 'aria-live="polite"' in page.text
    assert "Learning loop" in page.text
    assert 'id="correction-dialog"' in page.text

    capabilities = client.get("/v1/chat/capabilities").json()
    assert capabilities["observable_style_learning"] is True
    assert capabilities["individual_memory_revocation"] is True
    assert capabilities["optional_reference_slm"] is True
    assert capabilities["weight_training_inline"] is False
    assert capabilities["production_ready"] is False
