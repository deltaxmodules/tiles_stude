const chatLog = document.getElementById('chatLog');
const chatForm = document.getElementById('chatForm');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('sendBtn');
const traceList = document.getElementById('traceList');
const messages = [];

function addMessage(role, content, trace = null) {
  const wrapper = document.createElement('div');
  wrapper.className = `msg-wrap ${role}`;

  if (role === 'assistant' && trace) {
    const badge = document.createElement('div');
    const cacheClass = trace.cache === 'hit' ? 'hit' : 'miss';
    badge.className = `msg-badge ${cacheClass}`;
    const routeText = trace.route ?? 'none';
    badge.textContent = `cache ${trace.cache} | tile ${trace.tile} | route ${routeText} | model ${trace.model || 'n/a'}`;
    wrapper.appendChild(badge);
  }

  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.textContent = content;
  wrapper.appendChild(el);

  chatLog.appendChild(wrapper);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function renderTraceLines(lines) {
  traceList.innerHTML = '';
  lines.forEach((line, i) => {
    const li = document.createElement('li');
    li.className = 'trace-item done';
    li.textContent = `${i + 1}. ${line}`;
    traceList.appendChild(li);
  });
}

function setWorkingTrace() {
  renderTraceLines([
    'Routing request to specialist tile...',
    'Checking semantic cache...',
    'Generating response from model backend...',
  ]);
}

function renderBackendTrace(trace) {
  if (!trace) {
    renderTraceLines(['No backend trace available for this response.']);
    return;
  }
  const lines = [
    `Route: ${trace.route ?? 'none'} | Tile: ${trace.tile} | Model: ${trace.model || 'n/a'}`,
    `Cache: ${trace.cache} | Warm tile: ${trace.warm}`,
    `Timing (ms) -> routing: ${trace.metrics_ms.routing}, cache: ${trace.metrics_ms.cache}, generation: ${trace.metrics_ms.generation}`,
  ];
  renderTraceLines(lines);
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = promptEl.value.trim();
  if (!text) return;

  addMessage('user', text);
  messages.push({ role: 'user', content: text });
  promptEl.value = '';
  sendBtn.disabled = true;
  setWorkingTrace();

  try {
    const res = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, stream: false, include_trace: true }),
    });

    if (!res.ok) {
      const err = await res.text();
      addMessage('assistant', `Error ${res.status}: ${err}`);
      renderTraceLines([`Request failed with HTTP ${res.status}.`]);
      return;
    }

    const data = await res.json();
    const content = data?.choices?.[0]?.message?.content ?? '(empty response)';
    addMessage('assistant', content, data.trace);
    messages.push({ role: 'assistant', content });
    renderBackendTrace(data.trace);
  } catch (err) {
    addMessage('assistant', `Request failed: ${err.message}`);
    renderTraceLines([`Network error: ${err.message}`]);
  } finally {
    sendBtn.disabled = false;
  }
});
