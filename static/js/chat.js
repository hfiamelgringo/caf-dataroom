document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');

  let sessionId = sessionStorage.getItem('chat_session') || crypto.randomUUID();
  sessionStorage.setItem('chat_session', sessionId);

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    appendMessage('user', query);
    input.value = '';
    input.disabled = true;

    const typing = showTyping();

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId }),
      });

      typing.remove();

      if (!res.ok) {
        appendMessage('assistant', 'Something went wrong. Please try again.');
        return;
      }

      const data = await res.json();
      appendMessage('assistant', data.answer, data.sources);
    } catch (err) {
      typing.remove();
      appendMessage('assistant', 'Connection error. Please try again.');
    } finally {
      input.disabled = false;
      input.focus();
    }
  });

  function appendMessage(role, text, sources) {
    const msg = document.createElement('div');
    msg.className = 'chat-msg chat-msg--' + role;

    const content = document.createElement('div');
    content.className = 'chat-msg__content';

    if (role === 'assistant') {
      content.innerHTML = renderMarkdown(text);
    } else {
      content.textContent = text;
    }

    msg.appendChild(content);

    if (sources && sources.length > 0) {
      const srcEl = document.createElement('div');
      srcEl.className = 'chat-msg__sources';
      srcEl.textContent = 'Sources: ' + sources.join(', ');
      msg.appendChild(srcEl);
    }

    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'chat-typing';
    el.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  function renderMarkdown(text) {
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n{2,}/g, '</p><p>')
      .replace(/^(.+)$/gm, function (line) {
        if (line.startsWith('<')) return line;
        return line;
      })
      .replace(/^(?!<)(.+)$/gm, '<p>$1</p>')
      .replace(/<p><\/p>/g, '');
  }
});
