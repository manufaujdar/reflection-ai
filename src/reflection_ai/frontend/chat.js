"use strict";

const state = {
  sessionId: localStorage.getItem("reflection.session"),
  userId: localStorage.getItem("reflection.user"),
  question: null,
  sending: false,
  correctionMessageId: null,
};

const byId = (id) => document.getElementById(id);
const welcome = byId("welcome");
const onboarding = byId("onboarding");
const chat = byId("chat");
const messages = byId("messages");
const toast = byId("toast");

function showToast(text) {
  toast.textContent = text;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {"content-type": "application/json", ...(options.headers || {})},
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch (_) { /* no JSON */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

function showPanel(panel) {
  [welcome, onboarding, chat].forEach((item) => item.classList.toggle("hidden", item !== panel));
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderQuestion(data) {
  state.question = data.next_question;
  if (data.complete || !state.question) {
    enterChat();
    return;
  }
  showPanel(onboarding);
  const number = data.progress + 1;
  byId("progress-label").textContent = `Question ${number} of ${data.total}`;
  byId("progress-bar").style.width = `${Math.round((number / data.total) * 100)}%`;
  byId("question-title").textContent = state.question.prompt;
  byId("skip-answer").classList.toggle("hidden", !state.question.optional);
  const control = byId("answer-control");
  clearChildren(control);
  if (state.question.answer_type === "choice") {
    const grid = element("div", "choice-grid");
    state.question.options.forEach((option, index) => {
      const wrap = element("div", "choice");
      const input = element("input");
      input.type = "radio";
      input.name = "answer";
      input.id = `answer-${index}`;
      input.value = option;
      input.required = true;
      const label = element("label", "", option);
      label.htmlFor = input.id;
      wrap.append(input, label);
      grid.append(wrap);
    });
    control.append(grid);
  } else {
    const input = element("textarea", "answer-text");
    input.name = "answer";
    input.id = "text-answer";
    input.maxLength = 5000;
    input.required = true;
    input.placeholder = state.question.optional ? "Type an answer, or skip" : "Type your answer";
    control.append(input);
    input.focus();
  }
}

async function submitAnswer(skip = false) {
  if (!state.question) return;
  const selected = document.querySelector('[name="answer"]:checked');
  const textInput = document.querySelector('textarea[name="answer"]');
  const answer = selected ? selected.value : (textInput ? textInput.value : "");
  try {
    const result = await api(`/v1/chat/sessions/${state.sessionId}/onboarding`, {
      method: "POST",
      body: JSON.stringify({question_id: state.question.id, answer, skip}),
    });
    renderQuestion(result);
  } catch (error) { showToast(error.message); }
}

function renderEmptyChat() {
  clearChildren(messages);
  const empty = element("div", "empty-chat");
  empty.append(
    element("div", "assistant-orb", "R"),
    element("h2", "", "Ready when you are."),
    element("p", "", "I’ll use your explicit preferences now and gradually learn only the observable mechanics of how you write. You can inspect or delete everything at any time."),
  );
  messages.append(empty);
}

function addFeedbackActions(container, messageId) {
  const actions = element("div", "message-actions");
  const helpful = element("button", "", "Helpful");
  helpful.type = "button";
  helpful.addEventListener("click", () => submitFeedback(messageId, 1));
  const improve = element("button", "", "Correct this");
  improve.type = "button";
  improve.addEventListener("click", () => openCorrection(messageId));
  actions.append(helpful, improve);
  container.append(actions);
}

function addMessage(message, feedback = true) {
  const empty = messages.querySelector(".empty-chat");
  if (empty) empty.remove();
  const row = element("article", `message-row ${message.role}`);
  row.dataset.messageId = message.id;
  const content = element("div", "bubble", message.content);
  row.append(content);
  if (message.role === "assistant" && feedback) addFeedbackActions(content, message.id);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
}

async function loadHistory() {
  const history = await api(`/v1/chat/sessions/${state.sessionId}/messages`);
  if (!history.length) renderEmptyChat();
  else {
    clearChildren(messages);
    history.forEach((message) => addMessage(message));
  }
}

async function enterChat() {
  showPanel(chat);
  await loadHistory();
  byId("message-input").focus();
  refreshInspector();
}

async function sendMessage(text) {
  if (state.sending) return;
  state.sending = true;
  byId("send-button").disabled = true;
  const temporary = {id: crypto.randomUUID(), role: "user", content: text};
  addMessage(temporary, false);
  const pendingId = crypto.randomUUID();
  addMessage({id: pendingId, role: "assistant", content: "Thinking"}, false);
  const pendingNode = messages.querySelector(`[data-message-id="${pendingId}"]`);
  if (pendingNode) pendingNode.classList.add("pending");
  try {
    const result = await api(`/v1/chat/sessions/${state.sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({message: text, request_id: crypto.randomUUID()}),
    });
    const tempNode = messages.querySelector(`[data-message-id="${temporary.id}"]`);
    if (tempNode) tempNode.dataset.messageId = result.user_message.id;
    if (pendingNode) pendingNode.remove();
    addMessage(result.assistant_message);
    refreshInspector();
  } catch (error) {
    if (pendingNode) pendingNode.remove();
    showToast(error.message);
  } finally {
    state.sending = false;
    byId("send-button").disabled = false;
  }
}

function openCorrection(messageId) {
  state.correctionMessageId = messageId;
  byId("correction-input").value = "";
  byId("correction-dialog").showModal();
  byId("correction-input").focus();
}

async function submitFeedback(messageId, rating, correction = null) {
  try {
    await api(`/v1/chat/messages/${messageId}/feedback`, {
      method: "POST",
      body: JSON.stringify({rating, correction}),
    });
    showToast(correction ? "Correction learned as explicit memory" : "Feedback recorded");
    refreshInspector();
  } catch (error) { showToast(error.message); }
}

function renderInspector(data) {
  state.userId = data.user_id;
  localStorage.setItem("reflection.user", data.user_id);
  const readiness = Math.min(
    100,
    Math.round((data.learning.positive_examples / data.learning.minimum_examples) * 100),
  );
  byId("learning-badge").textContent = data.learning.enabled ? "Learning on" : "Paused";
  byId("learning-badge").classList.toggle("active", data.learning.enabled);
  byId("learning-summary").textContent = data.learning.training_consent
    ? "Immediate memory learning is separate from evaluation-gated weight training."
    : "Immediate personalization is active; model-weight training has no consent.";
  byId("readiness-bar").style.width = `${readiness}%`;
  byId("readiness-label").textContent = `${data.learning.positive_examples} of ${data.learning.minimum_examples} positively rated examples for dataset readiness`;
  byId("learning-toggle").checked = data.learning.enabled;
  byId("model-status").textContent = `${data.learning.live_provider} · ${data.learning.live_model}`;
  const modelDetails = byId("model-details");
  clearChildren(modelDetails);
  [
    ["Current response path", "Memory + provider"],
    ["Dataset", data.learning.dataset_ready ? "Ready to prepare" : "Not ready"],
    ["Latest training run", data.learning.latest_training_status],
    ["Reference SLM", "Experimental · not routed"],
  ].forEach(([label, value]) => {
    const row = element("div", "model-detail");
    row.append(element("span", "", label), element("strong", "", value));
    modelDetails.append(row);
  });
  byId("style-summary").textContent = data.style.sample_count
    ? `${data.style.sample_count} writing sample${data.style.sample_count === 1 ? "" : "s"} · profile v${data.style.version}`
    : "No conversation samples yet.";
  const styles = byId("style-list");
  clearChildren(styles);
  data.style.instructions.forEach((instruction) => styles.append(element("span", "chip", instruction)));
  const memoryList = byId("memory-list");
  clearChildren(memoryList);
  if (!data.memories.length) memoryList.append(element("p", "muted", "Nothing retained yet."));
  data.memories.forEach((memory) => {
    const item = element("div", "memory-item");
    const copy = element("div", "memory-copy");
    copy.append(element("strong", "", `${memory.type} · ${memory.explicit ? "explicit" : "inferred"}`), element("span", "", memory.content));
    const forget = element("button", "forget-button", "Forget");
    forget.type = "button";
    forget.addEventListener("click", () => forgetMemory(memory.id));
    item.append(copy, forget);
    memoryList.append(item);
  });
  const trace = byId("trace-list");
  clearChildren(trace);
  const latest = data.recent_agent_runs[0];
  if (!latest) trace.append(element("span", "muted", "No agent run yet."));
  else latest.trace.stages.forEach((stage) => trace.append(element("div", "trace-step", stage.replaceAll("-", " "))));
}

async function forgetMemory(memoryId) {
  if (!window.confirm("Forget this memory? Its audit history remains, but it will stop affecting responses.")) return;
  try {
    await api(`/v1/chat/sessions/${state.sessionId}/memories/${memoryId}`, {method: "DELETE"});
    showToast("Memory revoked");
    refreshInspector();
  } catch (error) { showToast(error.message); }
}

async function setLearning(enabled) {
  try {
    await api(`/v1/chat/sessions/${state.sessionId}/learning`, {
      method: "PATCH",
      body: JSON.stringify({enabled}),
    });
    showToast(enabled ? "Learning resumed" : "New learning paused");
    refreshInspector();
  } catch (error) {
    byId("learning-toggle").checked = !enabled;
    showToast(error.message);
  }
}

async function refreshInspector() {
  if (!state.sessionId) return;
  try { renderInspector(await api(`/v1/chat/sessions/${state.sessionId}/personalization`)); }
  catch (_) { /* session may have been erased */ }
}

function setInspector(open) {
  byId("inspector").classList.toggle("open", open);
  byId("inspector").setAttribute("aria-hidden", String(!open));
  byId("inspector-toggle").setAttribute("aria-expanded", String(open));
  if (open) refreshInspector();
}

async function eraseAllData() {
  if (!state.userId || !window.confirm("Permanently delete this local profile, messages, memories, evidence, and traces?")) return;
  try {
    await api(`/v1/users/${state.userId}`, {method: "DELETE"});
    localStorage.removeItem("reflection.session");
    localStorage.removeItem("reflection.user");
    state.sessionId = null;
    state.userId = null;
    setInspector(false);
    showPanel(welcome);
    showToast("All profile data deleted");
  } catch (error) { showToast(error.message); }
}

byId("start-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const session = await api("/v1/chat/sessions", {
      method: "POST",
      body: JSON.stringify({
        external_user_id: byId("display-id").value.trim(),
        consent: byId("consent").checked,
        training_consent: byId("training-consent").checked,
      }),
    });
    state.sessionId = session.id;
    state.userId = session.user_id;
    localStorage.setItem("reflection.session", session.id);
    localStorage.setItem("reflection.user", session.user_id);
    renderQuestion({progress: session.onboarding_index, total: session.onboarding_total, next_question: session.next_question, complete: session.status !== "onboarding"});
  } catch (error) { showToast(error.message); }
});

byId("answer-form").addEventListener("submit", (event) => { event.preventDefault(); submitAnswer(false); });
byId("skip-answer").addEventListener("click", () => submitAnswer(true));
byId("composer").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = byId("message-input");
  const text = input.value.trim();
  if (text) { input.value = ""; input.style.height = "auto"; sendMessage(text); }
});
byId("message-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); byId("composer").requestSubmit(); }
});
byId("message-input").addEventListener("input", (event) => {
  event.target.style.height = "auto";
  event.target.style.height = `${Math.min(event.target.scrollHeight, 180)}px`;
});
byId("inspector-toggle").addEventListener("click", () => setInspector(!byId("inspector").classList.contains("open")));
byId("inspector-close").addEventListener("click", () => setInspector(false));
byId("learning-toggle").addEventListener("change", (event) => setLearning(event.target.checked));
byId("erase-data").addEventListener("click", eraseAllData);
byId("erase-onboarding").addEventListener("click", eraseAllData);
byId("correction-cancel").addEventListener("click", () => byId("correction-dialog").close());
byId("correction-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const correction = byId("correction-input").value.trim();
  if (!correction || !state.correctionMessageId) return;
  byId("correction-dialog").close();
  submitFeedback(state.correctionMessageId, -1, correction);
  state.correctionMessageId = null;
});

(async function restore() {
  if (!state.sessionId) return;
  try {
    const session = await api(`/v1/chat/sessions/${state.sessionId}`);
    state.userId = session.user_id;
    if (session.status === "onboarding") {
      renderQuestion({progress: session.onboarding_index, total: session.onboarding_total, next_question: session.next_question, complete: false});
    } else if (session.status === "active") await enterChat();
    else showPanel(welcome);
  } catch (_) {
    localStorage.removeItem("reflection.session");
    localStorage.removeItem("reflection.user");
  }
}());
