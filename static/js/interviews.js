// Sortable + filterable table for the interviews library.
// All client-side; no framework. Operates on data-* attributes set by the template.

(function () {
  const tbody = document.getElementById('iv-tbody');
  if (!tbody) return;

  const search = document.getElementById('iv-search');
  const countEl = document.getElementById('iv-count');
  const emptyEl = document.getElementById('iv-empty');
  const clearBtn = document.getElementById('iv-clear');
  const chips = Array.from(document.querySelectorAll('.iv-chip'));
  const sortHeaders = Array.from(document.querySelectorAll('.iv-sort'));

  // active filters: { country: Set, topic: Set, source: Set }
  const active = { country: new Set(), topic: new Set(), source: new Set() };
  let sortKey = 'date';
  let sortDir = 'desc';

  function rowMatches(row) {
    // Country / topic / source — multi-select OR within group, AND across groups
    for (const filter of ['country', 'topic', 'source']) {
      const set = active[filter];
      if (set.size === 0) continue;
      const attrName = filter === 'source' ? 'source' : filter + 's';
      const raw = row.dataset[attrName] || '';
      const values = raw ? raw.split('|') : [];
      let matched = false;
      for (const v of set) {
        if (values.includes(v)) { matched = true; break; }
      }
      if (!matched) return false;
    }
    // Free-text search
    const q = (search.value || '').trim().toLowerCase();
    if (q && !row.dataset.search.includes(q)) return false;
    return true;
  }

  function applyFilters() {
    const rows = Array.from(tbody.querySelectorAll('.iv-row'));
    let visible = 0;
    rows.forEach(r => {
      const m = rowMatches(r);
      r.hidden = !m;
      if (m) visible++;
    });
    countEl.textContent = visible;
    emptyEl.hidden = visible !== 0;
    const anyFilter = active.country.size + active.topic.size + active.source.size + (search.value ? 1 : 0);
    clearBtn.hidden = anyFilter === 0;
  }

  function applySort() {
    const rows = Array.from(tbody.querySelectorAll('.iv-row'));
    rows.sort((a, b) => {
      const av = a.dataset[sortKey] || '';
      const bv = b.dataset[sortKey] || '';
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    rows.forEach(r => tbody.appendChild(r));
    sortHeaders.forEach(h => {
      h.classList.remove('iv-sort--active', 'iv-sort--asc', 'iv-sort--desc');
      if (h.dataset.sort === sortKey) {
        h.classList.add('iv-sort--active', 'iv-sort--' + sortDir);
      }
    });
  }

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const filter = chip.dataset.filter;
      const value = chip.dataset.value;
      if (active[filter].has(value)) {
        active[filter].delete(value);
        chip.classList.remove('iv-chip--active');
      } else {
        active[filter].add(value);
        chip.classList.add('iv-chip--active');
      }
      applyFilters();
    });
  });

  sortHeaders.forEach(h => {
    h.addEventListener('click', () => {
      const key = h.dataset.sort;
      if (sortKey === key) {
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        sortKey = key;
        sortDir = key === 'date' ? 'desc' : 'asc';
      }
      applySort();
    });
  });

  search.addEventListener('input', applyFilters);

  clearBtn.addEventListener('click', () => {
    Object.values(active).forEach(s => s.clear());
    chips.forEach(c => c.classList.remove('iv-chip--active'));
    search.value = '';
    applyFilters();
  });

  applySort();
})();
