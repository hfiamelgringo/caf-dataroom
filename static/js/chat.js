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
      appendMessage('assistant', data.answer, data.source_links || data.sources || []);
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
      content.innerHTML = renderMarkdown(text, sources);
    } else {
      content.textContent = text;
    }

    msg.appendChild(content);

    if (sources && sources.length > 0) {
      const srcEl = document.createElement('div');
      srcEl.className = 'chat-msg__sources';
      const label = document.createElement('span');
      label.textContent = 'Sources: ';
      srcEl.appendChild(label);
      sources.forEach((s, i) => {
        if (i > 0) srcEl.appendChild(document.createTextNode(', '));
        if (typeof s === 'string') {
          srcEl.appendChild(document.createTextNode(s));
        } else if (s.url) {
          const a = document.createElement('a');
          a.href = s.url;
          a.textContent = s.title || s.stakeholder || s.slug;
          a.className = 'chat-msg__source-link';
          srcEl.appendChild(a);
        } else {
          srcEl.appendChild(document.createTextNode(s.title || s.slug || '?'));
        }
      });
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

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function citationReplacements(sources) {
    // Each source contributes patterns that match the LLM's bracketed citation forms.
    // Org strings can be paraphrased (e.g. "Practical VC" vs the canonical long form),
    // so we match any non-bracket text between the stakeholder name and the closing bracket.
    const replacements = [];
    if (!sources) return replacements;
    sources.forEach(s => {
      if (typeof s === 'string' || !s.url) return;
      const stake = (s.stakeholder || '').trim();
      if (!stake) return;
      replacements.push({
        pattern: new RegExp('\\[' + escapeRegex(stake) + ',\\s*[^\\]]+\\]', 'g'),
        url: s.url,
      });
      replacements.push({
        pattern: new RegExp('\\[' + escapeRegex(stake) + '\\]', 'g'),
        url: s.url,
      });
    });
    return replacements;
  }

  function linkifyCitations(html, sources) {
    // Runs AFTER marked has produced HTML. Replaces each known citation with an
    // anchor; strips any remaining [Word Word] / [Section Title] brackets that
    // didn't match a source so they render as plain text without brackets.
    const replacements = citationReplacements(sources);
    let out = html;
    replacements.forEach(({ pattern, url }) => {
      out = out.replace(pattern, function (match) {
        const label = match.slice(1, -1);
        return '<a href="' + escapeHtml(url) + '" class="chat-msg__cite">' + escapeHtml(label) + '</a>';
      });
    });
    // Strip orphan brackets — only those that look like citation candidates
    // (start with capital letter, contain words/spaces/commas/&/-/.).
    out = out.replace(/\[([A-Z][^\[\]\n]{1,80})\]/g, '$1');
    return out;
  }

  function renderMarkdown(text, sources) {
    if (typeof window.marked === 'undefined') {
      // Fallback: minimal escape so nothing renders as raw HTML.
      const safe = escapeHtml(text);
      return linkifyCitations(safe, sources);
    }
    const html = window.marked.parse(text, { breaks: true, gfm: true });
    return linkifyCitations(html, sources);
  }
});
