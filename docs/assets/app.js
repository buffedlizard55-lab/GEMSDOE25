// Copy a research identifier, not an authorization to submit a TIFF.
document.addEventListener('click', function (e) {
  var b = e.target.closest('[data-copy]');
  if (!b) return;
  var el = document.getElementById(b.getAttribute('data-copy'));
  if (!el) return;
  var txt = el.textContent.trim();
  var done = function () { var o = b.textContent; b.textContent = 'Copied ✓'; setTimeout(function () { b.textContent = o; }, 1800); };
  if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(txt).then(done); }
  else { var r = document.createRange(); r.selectNodeContents(el); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); try { document.execCommand('copy'); done(); } catch (x) {} }
});

// The timestamped local feed is historical, not a live leaderboard. Render
// external metadata as text instead of HTML and reject unsafe link schemes.
(function () {
  var host = document.getElementById('feed');
  if (!host) return;
  var base = host.getAttribute('data-base') || '';
  function cell(row, text) {
    var td = document.createElement('td');
    td.textContent = text || '';
    row.appendChild(td);
    return td;
  }
  fetch(base + 'data/feed.json', { cache: 'no-store' }).then(function (r) {
    if (!r.ok) throw new Error('feed unavailable');
    return r.json();
  }).then(function (f) {
    if (!Array.isArray(f.items)) throw new Error('invalid feed');
    host.replaceChildren();
    var description = document.createElement('p');
    description.className = 'small';
    description.textContent = 'Historical feed generated ' + (f.generated_utc || 'unknown') +
      ' by ' + (f.generator || 'unknown') + '. ' + (f.policy || '');
    host.appendChild(description);
    var table = document.createElement('table');
    var header = document.createElement('tr');
    ['Source', 'Status', 'Detail'].forEach(function (name) {
      var th = document.createElement('th');
      th.textContent = name;
      header.appendChild(th);
    });
    var thead = document.createElement('thead');
    thead.appendChild(header);
    table.appendChild(thead);
    var body = document.createElement('tbody');
    f.items.forEach(function (item) {
      var row = document.createElement('tr');
      var title = cell(row, item.title);
      try {
        var url = new URL(item.url, document.baseURI);
        if (url.protocol === 'https:' || url.protocol === 'http:') {
          var a = document.createElement('a');
          a.href = url.href;
          a.textContent = item.title || '';
          title.replaceChildren(a);
        }
      } catch (ignore) { /* Invalid URLs remain plain text. */ }
      cell(row, item.status);
      cell(row, item.detail).className = 'small';
      body.appendChild(row);
    });
    table.appendChild(body);
    host.appendChild(table);
  }).catch(function () { host.textContent = 'Feed file not found or invalid; no current status is implied.'; });
})();
