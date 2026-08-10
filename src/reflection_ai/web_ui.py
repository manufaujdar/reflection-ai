"""Maintainable local-only synthetic interaction console for the research API."""

CONSOLE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Reflection AI research console · local</title>
  <style>
    :root {
      --ink: #24322d;
      --muted: #5d6d66;
      --paper: #f7f5ef;
      --surface: #fffef9;
      --line: #d7ddd8;
      --accent: #245c4a;
      --accent-dark: #173f33;
      --warning: #7d3b22;
      --warning-bg: #fff2e8;
      --focus: #1769aa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font: 16px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    a { color: var(--accent-dark); }
    a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible,
    summary:focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
    header, main, footer { width: min(920px, calc(100% - 2rem)); margin-inline: auto; }
    header { padding: 2rem 0 1rem; }
    .eyebrow { color: var(--accent); font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
    h1 { margin: .15rem 0 .35rem; font-size: clamp(2rem, 5vw, 3rem); line-height: 1.1; }
    .lede, .muted { color: var(--muted); }
    .trust {
      border-left: 5px solid var(--warning);
      background: var(--warning-bg);
      padding: 1rem 1.1rem;
      margin: 1rem 0 1.5rem;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: .45rem;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface);
      padding: .35rem .7rem;
      color: var(--muted);
      font-size: .9rem;
    }
    .status-pill::before { content: ""; width: .55rem; height: .55rem; border-radius: 50%; background: var(--accent); }
    section, details {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: clamp(1rem, 3vw, 1.5rem);
      margin-bottom: 1rem;
    }
    h2 { margin-top: 0; font-size: 1.25rem; }
    label { display: block; font-weight: 700; margin: 1rem 0 .35rem; }
    input, textarea {
      width: 100%;
      border: 1px solid #9aa8a1;
      border-radius: 8px;
      background: white;
      color: var(--ink);
      font: inherit;
      padding: .75rem;
    }
    textarea { min-height: 7rem; resize: vertical; }
    .actions { display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1rem; }
    button {
      border: 1px solid var(--accent);
      border-radius: 8px;
      background: transparent;
      color: var(--accent-dark);
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      padding: .7rem 1rem;
    }
    button.primary { background: var(--accent); color: white; }
    button.danger { border-color: var(--warning); color: var(--warning); }
    button:hover:not(:disabled) { box-shadow: 0 2px 8px rgb(20 50 40 / 15%); }
    button:disabled { cursor: not-allowed; opacity: .45; }
    summary { cursor: pointer; font-weight: 700; }
    pre {
      min-height: 6rem;
      overflow: auto;
      border-radius: 8px;
      background: #edf1ee;
      padding: 1rem;
      white-space: pre-wrap;
      word-break: break-word;
    }
    footer { padding: 1rem 0 2.5rem; color: var(--muted); font-size: .92rem; }
    @media (max-width: 560px) {
      header { padding-top: 1.25rem; }
      .actions { align-items: stretch; flex-direction: column; }
      button { width: 100%; }
    }
    @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Local research prototype</div>
    <h1>Reflection AI</h1>
    <p class="lede">Exercise the consent, evidence, memory, and deletion flow with synthetic data.</p>
    <span class="status-pill">Local API · mock model by default</span>
  </header>
  <main>
    <aside class="trust" aria-label="Research safety warning">
      <strong>Not production-ready.</strong> Authentication and tenant isolation are not implemented;
      tenant authorization is also absent.
      Never enter real personal, patient, credential, confidential, or proprietary information.
    </aside>

    <section aria-labelledby="setup-title">
      <h2 id="setup-title">1. Create a disposable subject</h2>
      <p class="muted">A timestamp is appended so repeated tests remain isolated.</p>
      <form id="subject-form">
        <label for="external">Synthetic subject ID</label>
        <input id="external" value="synthetic-browser-subject" autocomplete="off" required>
        <div class="actions">
          <button class="primary" type="submit">Create consented subject</button>
        </div>
      </form>
    </section>

    <section aria-labelledby="preference-title">
      <h2 id="preference-title">2. Add an explicit preference</h2>
      <p class="muted">The value becomes evidence and an auditable memory proposal. Use synthetic wording only.</p>
      <form id="preference-form">
        <label for="preference">Synthetic preference or correction</label>
        <textarea id="preference" required>I prefer concise explanations with a short example.</textarea>
        <div class="actions">
          <button class="primary" id="add" type="submit" disabled>Add preference event</button>
          <button class="danger" id="remove" type="button" disabled>Delete synthetic subject</button>
        </div>
      </form>
    </section>

    <section aria-labelledby="result-title">
      <h2 id="result-title">API result</h2>
      <pre id="result" role="status" aria-live="polite">No subject created.</pre>
    </section>

    <details>
      <summary>Method and framework capabilities</summary>
      <p>Inspect the machine-readable capability boundary or the full API contract.</p>
      <div class="actions">
        <button id="capabilities" type="button">Load capabilities</button>
        <a href="/docs">Open API documentation</a>
      </div>
    </details>
  </main>
  <footer>
    Data entered here is sent to the local Reflection AI process. This console does not prove that the
    process is private, authenticated, encrypted, or safely configured. Review
    <a href="https://github.com/manufaujdar/reflection-ai">source and deployment boundaries</a> first.
  </footer>
  <script>
    let user = null;
    const output = document.querySelector("#result");
    const addButton = document.querySelector("#add");
    const removeButton = document.querySelector("#remove");

    function setSubject(nextUser) {
      user = nextUser;
      addButton.disabled = !user;
      removeButton.disabled = !user;
    }

    async function showResponse(response) {
      let body;
      try {
        body = response.status === 204 ? { deleted: true } : await response.json();
      } catch (_error) {
        body = { detail: "The local API returned a non-JSON response." };
      }
      output.textContent = JSON.stringify({ status: response.status, ...body }, null, 2);
      return body;
    }

    document.querySelector("#subject-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      output.textContent = "Creating synthetic subject…";
      try {
        const externalId = `${document.querySelector("#external").value}-${Date.now()}`;
        const response = await fetch("/v1/users", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            external_id: externalId,
            application_id: "local-console",
            tenant_id: "synthetic-only",
            consent: true,
            training_consent: false,
            attributes: { learning_enabled: true }
          })
        });
        const body = await showResponse(response);
        if (response.ok) setSubject(body);
      } catch (error) {
        output.textContent = `Local API unavailable: ${String(error)}`;
      }
    });

    document.querySelector("#preference-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!user) return;
      output.textContent = "Adding synthetic evidence…";
      try {
        await showResponse(await fetch(`/v1/users/${user.id}/events`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            kind: "preference",
            input_text: document.querySelector("#preference").value,
            source: "local-console",
            idempotency_key: `browser-${Date.now()}`
          })
        }));
      } catch (error) {
        output.textContent = `Local API unavailable: ${String(error)}`;
      }
    });

    removeButton.addEventListener("click", async () => {
      if (!user || !window.confirm("Delete this synthetic subject and its local records?")) return;
      try {
        await showResponse(await fetch(`/v1/users/${user.id}`, { method: "DELETE" }));
        setSubject(null);
      } catch (error) {
        output.textContent = `Local API unavailable: ${String(error)}`;
      }
    });

    document.querySelector("#capabilities").addEventListener("click", async () => {
      try {
        await showResponse(await fetch("/v1/capabilities"));
      } catch (error) {
        output.textContent = `Local API unavailable: ${String(error)}`;
      }
    });
  </script>
</body>
</html>
"""
