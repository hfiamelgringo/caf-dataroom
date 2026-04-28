// Sortable table + country dropdown filter for the interviews library.
// Tags (topics, source type) live in frontmatter for chat routing only — not in the UI.

(function () {
  const tbody = document.getElementById('iv-tbody');
  if (!tbody) return;

  const countrySelect = document.getElementById('iv-country');
  const countEl = document.getElementById('iv-count');
  const emptyEl = document.getElementById('iv-empty');
  const sortHeaders = Array.from(document.querySelectorAll('.iv-sort'));

  let sortKey = 'stakeholder';
  let sortDir = 'asc';

  function rowMatches(row) {
    const country = (countrySelect.value || '').trim();
    if (!country) return true;
    const values = (row.dataset.countries || '').split('|');
    return values.includes(country);
  }

  function applyFilter() {
    const rows = Array.from(tbody.querySelectorAll('.iv-row'));
    let visible = 0;
    rows.forEach(r => {
      const m = rowMatches(r);
      r.hidden = !m;
      if (m) visible++;
    });
    if (countEl) countEl.textContent = visible;
    if (emptyEl) emptyEl.hidden = visible !== 0;
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

  countrySelect.addEventListener('change', applyFilter);

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

  applySort();
})();
