from __future__ import annotations


class ByteTokenizer:
    """Deterministic UTF-8 tokenizer for reproducible research and tests.

    A production model should use the tokenizer shipped with its base checkpoint.
    Byte-level encoding is intentionally simple and has no learned vocabulary.
    """

    pad_token_id = 0
    bos_token_id = 1
    eos_token_id = 2
    byte_offset = 3
    vocab_size = 259

    def encode(
        self,
        text: str,
        *,
        add_bos: bool = False,
        add_eos: bool = False,
        max_length: int | None = None,
    ) -> list[int]:
        tokens = [value + self.byte_offset for value in text.encode("utf-8")]
        if add_bos:
            tokens.insert(0, self.bos_token_id)
        if add_eos:
            tokens.append(self.eos_token_id)
        if max_length is not None:
            if max_length < 0:
                raise ValueError("max_length cannot be negative")
            tokens = tokens[:max_length]
            if add_eos and tokens and tokens[-1] != self.eos_token_id:
                tokens[-1] = self.eos_token_id
        return tokens

    def decode(self, token_ids: list[int], *, skip_special_tokens: bool = True) -> str:
        values: list[int] = []
        for token_id in token_ids:
            if token_id in {self.pad_token_id, self.bos_token_id, self.eos_token_id}:
                if skip_special_tokens:
                    continue
                raise ValueError("Special tokens cannot be decoded as UTF-8 bytes")
            value = token_id - self.byte_offset
            if not 0 <= value <= 255:
                raise ValueError(f"Token {token_id} is outside the byte vocabulary")
            values.append(value)
        return bytes(values).decode("utf-8", errors="replace")
