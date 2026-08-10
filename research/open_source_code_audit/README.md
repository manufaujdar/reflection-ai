# Open-source code audit

This folder is a reproducible technical index of personalization-related open-source repositories reviewed for Reflection AI. It does not duplicate upstream source code. Each snapshot is pinned by commit SHA and represented by:

- `metadata.json`: origin, commit, branch, date, and inventory totals.
- `manifest.tsv`: every tracked file with type, size, line counts, approximate code/comment/blank counts, and SHA-256.
- `line_index.tsv.gz`: every line of every textual tracked file with path, line number, classification, byte count, and SHA-256. It deliberately stores hashes rather than upstream source text.
- `directory_summary.tsv`: aggregate size and line statistics for every directory.
- `symbols.tsv`: functions, classes, interfaces, types, and other declarations with source line numbers.
- `relevant_files.tsv`: all paths matching personalization, memory, retrieval, reflection, evaluation, privacy, and training concepts.
- `SUMMARY.md`: human-reviewed architecture, important execution paths, and reuse guidance.

The indexes cover every tracked file and make source changes detectable at file and symbol level. Human summaries focus on code that can materially influence Reflection AI. Generated code, assets, fixtures, vendored dependencies, and unrelated product UI are inventoried but not paraphrased line by line.

Inspect a line ledger without extracting it:

```bash
gzip -dc research/open_source_code_audit/repos/mem0/line_index.tsv.gz | less
```

Run the generator against shallow clones:

```bash
python3 research/open_source_code_audit/generate_indexes.py \
  --sources /tmp/reflection-open-source-audit
```

Raw sources remain upstream or in temporary clones. Consult each repository's license before reuse.
