# Third-party reuse and notices

Reflection AI currently does not vendor source files from the reviewed repositories. It reuses selected projects through optional published packages and their documented public APIs. Their source, copyright, license, and security updates remain upstream.

| Component | Use | License | Source |
|---|---|---|---|
| Mem0 (`mem0ai`) | Optional memory backend | Apache License 2.0 | https://github.com/mem0ai/mem0 |
| Hindsight (`hindsight-client`) | Optional retain/recall backend | MIT License | https://github.com/vectorize-io/hindsight |

Projects reviewed but not distributed as dependencies or copied into the runtime:

- Graphiti (Apache-2.0): planned optional temporal-graph backend.
- Letta (Apache-2.0): architectural reference for user/persona memory and background learning.
- LangMem (MIT): architectural reference for hot-path and background memory management.
- Supermemory (MIT): architectural and benchmark reference.
- Khoj (AGPL-3.0): product and local-first UX reference only; no code copied.
- LaMP: research/benchmark reference only; no code or datasets copied.

Before distributing a release, generate a dependency SBOM and bundle the exact license texts for installed optional packages. This document is an engineering inventory, not legal advice.
