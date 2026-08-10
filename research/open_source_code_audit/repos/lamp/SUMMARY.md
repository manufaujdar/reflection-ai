# LaMP source review

Snapshot: `38c9d4d87629aba5a821bcddc10ddcc83f8d49a1` (2025-02-18). Inventory: 51 files, 5,059 text lines, 273 declarations. No root license file was found in the audited snapshot, so source copying should be treated as unauthorized until terms are clarified; papers, algorithms and experimental findings can still guide independent implementation.

## Architecture and experiment path

LaMP provides seven personalized classification/generation tasks where each example includes a user profile. `LaMP/rank_profiles.py` converts task-specific profile records into query/corpus text and ranks every profile using BM25, Contriever embeddings or recency. Ranked items are merged into datasets and prompt templates select the first *k* items for training/evaluation.

The repository also compares and optimizes personalization methods. ROPG trains a retriever using downstream generation reward. RSPG/distillation code uses generation behavior to supervise selection. PEFT experiments test parameter-efficient user adaptation and combinations with retrieval. Evaluation dispatches task-appropriate metrics: accuracy/macro-F1, MAE/RMSE or ROUGE. Profile/retriever utilization scorers test whether generations actually use supplied profile information rather than merely receiving it.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `LaMP/rank_profiles.py` | BM25, Contriever and recency profile ranking | Reimplement as baseline retrieval strategies with our typed memories and temporal scoring. |
| `LaMP/train_llm.py` / `evaluate_llm.py` | RAG prompt construction and model experiments | Inform reproducible experiment configuration, not production serving. |
| `LaMP/profile_item_utilization_scorer.py` | Whether output reflects supplied profile items | Build an evidence-attribution/personalization-use metric. |
| `LaMP/retriever_utilization_scorer.py` | Retriever impact measurement | Compare retrieved, oracle and random context. |
| `ROPG/models/retriever.py` and training scripts | Reward-optimized retrieval | Consider after a stable offline reward metric exists. |
| `PEFT/*` | User-level parameter-efficient tuning experiments | Gate behind data sufficiency, privacy and rollback requirements. |
| `eval/evaluation.py` | Per-task metric selection and ID validation | Adapt the baseline-versus-personalized evaluation structure. |

## Strengths, gaps and decision

LaMP prevents the project from equating “has memory” with “is personalized.” It demands comparative experiments and shows that retrieval, recency, profile volume and parameter adaptation have different regimes. Reflection AI needs the same ablations: no profile, recent only, semantic/lexical retrieval, oracle evidence, adapter only and combined.

The code is research-oriented, assumes task-specific JSON and GPU scripts, and lacks a detected root license. Independently implement the experiment protocol and metrics; do not copy source files until licensing is resolved.
