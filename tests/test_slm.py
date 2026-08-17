import asyncio
import importlib.util
import json

import pytest

from reflection_ai.slm import ByteTokenizer, GenerationConfig, SLMConfig


def tiny_config() -> SLMConfig:
    return SLMConfig(
        context_length=48,
        embedding_dim=32,
        attention_heads=4,
        layers=2,
        dropout=0,
        personalization_rank=4,
        personalization_alpha=8,
    )


def test_byte_tokenizer_is_deterministic_and_unicode_safe():
    tokenizer = ByteTokenizer()
    text = "Reflection नमस्ते 🌱"
    encoded = tokenizer.encode(text, add_bos=True, add_eos=True)
    assert encoded[0] == tokenizer.bos_token_id
    assert encoded[-1] == tokenizer.eos_token_id
    assert tokenizer.decode(encoded) == text
    assert tokenizer.vocab_size == 259


def test_slm_and_generation_configuration_fail_closed():
    with pytest.raises(ValueError, match="divisible"):
        SLMConfig(embedding_dim=30, attention_heads=8)
    with pytest.raises(ValueError, match="top_p"):
        GenerationConfig(top_p=1.1)
    assert len(tiny_config().fingerprint) == 64


TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_slm_uses_shifted_causal_loss_and_future_tokens_do_not_leak():
    import torch

    from reflection_ai.slm.model import ReflectionSLM

    torch.manual_seed(7)
    model = ReflectionSLM(tiny_config()).eval()
    first = torch.tensor([[1, 10, 11, 12, 13]])
    second = torch.tensor([[1, 10, 11, 12, 99]])
    first_logits, loss = model(first, labels=first)
    second_logits, _ = model(second)
    assert first_logits.shape == (1, 5, 259)
    assert loss is not None and torch.isfinite(loss)
    assert torch.allclose(first_logits[:, :4], second_logits[:, :4], atol=1e-6)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_personalization_freezes_base_and_exports_only_small_adapters():
    import torch

    from reflection_ai.slm.model import ReflectionSLM

    model = ReflectionSLM(tiny_config())
    summary = model.freeze_base_for_personalization()
    assert 0 < summary["trainable"] < summary["total"]
    assert all(
        (".adapter." in name) == parameter.requires_grad
        for name, parameter in model.named_parameters()
    )
    adapter = model.adapter_state_dict()
    assert adapter
    assert all(".adapter." in name for name in adapter)
    model.load_adapter_state_dict(adapter)
    with pytest.raises(ValueError, match="non-adapter"):
        model.load_adapter_state_dict({"language_head.weight": model.language_head.weight})
    incomplete = {name: value for index, (name, value) in enumerate(adapter.items()) if index}
    before = {name: value.clone() for name, value in model.adapter_state_dict().items()}
    with pytest.raises(ValueError, match="incomplete"):
        model.load_adapter_state_dict(incomplete)
    assert all(torch.equal(before[name], value) for name, value in model.adapter_state_dict().items())


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_personalization_strength_supports_base_comparison_and_fails_closed():
    import torch

    from reflection_ai.slm.model import ReflectionSLM

    model = ReflectionSLM(tiny_config()).eval()
    with torch.no_grad():
        model.blocks[0].adapter.up.weight.fill_(0.05)
    tokens = torch.tensor([[1, 12, 13]])
    base_logits, _ = model(tokens, personalization_strength=0)
    personal_logits, _ = model(tokens, personalization_strength=1)
    assert not torch.allclose(base_logits, personal_logits)
    with pytest.raises(ValueError, match="strength"):
        model(tokens, personalization_strength=-1)
    with pytest.raises(ValueError, match="strength"):
        model(tokens, personalization_strength=3)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_generation_validates_controls_and_supports_greedy_decoding():
    import torch

    from reflection_ai.slm.model import ReflectionSLM

    model = ReflectionSLM(tiny_config())
    prompt = torch.tensor([[1, 10, 11]])
    generated = model.generate(
        prompt,
        GenerationConfig(max_new_tokens=4, temperature=0, eos_token_id=258),
    )
    assert generated.shape == (1, 7)
    with pytest.raises(ValueError, match="non-empty"):
        model.generate(torch.empty((1, 0), dtype=torch.long))


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_reference_backend_trains_and_exports_adapter_with_provenance(tmp_path):
    import torch

    from reflection_ai.slm.checkpoints import save_base_checkpoint
    from reflection_ai.slm.model import ReflectionSLM
    from reflection_ai.slm.training import ReferenceSLMTrainingBackend

    config = tiny_config()
    torch.manual_seed(11)
    base = ReflectionSLM(config)
    base_path = tmp_path / "base.pt"
    provenance = save_base_checkpoint(base, base_path, base_model_id="synthetic-test-base")
    assert len(provenance["checkpoint_hash"]) == 64
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "prompt": "Give a short update",
                "completion": "Outcome first, then two bullets.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    backend = ReferenceSLMTrainingBackend(
        tmp_path / "artifacts",
        "a" * 32,
        config,
        epochs=1,
        device="cpu",
    )
    result = asyncio.run(backend.train(str(dataset), str(base_path)))
    checkpoint = torch.load(result["artifact_uri"], map_location="cpu", weights_only=True)
    assert checkpoint["format"] == "reflection-ai-adapter-v1"
    assert checkpoint["config_fingerprint"] == config.fingerprint
    assert all(".adapter." in name for name in checkpoint["adapter_state"])
    assert result["metrics"]["training_loss"] > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="install the slm extra for model tests")
def test_base_checkpoint_is_versioned_and_cannot_be_overwritten(tmp_path):
    import torch

    from reflection_ai.slm.checkpoints import save_base_checkpoint
    from reflection_ai.slm.model import ReflectionSLM

    target = tmp_path / "base.pt"
    model = ReflectionSLM(tiny_config())
    provenance = save_base_checkpoint(model, target, base_model_id="reference-random-v1")
    checkpoint = torch.load(target, map_location="cpu", weights_only=True)
    assert checkpoint["format"] == "reflection-ai-base-v1"
    assert checkpoint["config_fingerprint"] == tiny_config().fingerprint
    assert provenance["base_model_id"] == "reference-random-v1"
    with pytest.raises(FileExistsError, match="overwrite"):
        save_base_checkpoint(model, target, base_model_id="another-base")
