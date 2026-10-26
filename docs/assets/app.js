// Copy-to-clipboard controls and the optional, status-labeled source feed.
document.addEventListener('click', function (event) {
  var button = event.target.closest('[data-copy]');
  if (!button) return;
  var element = document.getElementById(button.getAttribute('data-copy'));
  if (!element) return;
  var text = element.textContent.trim();
  var done = function () {
    var oldLabel = button.textContent;
    button.textContent = 'Copied ✓';
    setTimeout(function () { button.textContent = oldLabel; }, 1800);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done);
  } else {
    var range = document.createRange();
    range.selectNodeContents(element);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    try { document.execCommand('copy'); done(); } catch (error) { /* clipboard is optional */ }
  }
});

(function () {
  var host = document.getElementById('feed');
  if (!host) return;
  var base = host.getAttribute('data-base') || '';
  fetch(base + 'data/feed.json', { cache: 'no-store' })
    .then(function (response) {
      if (!response.ok) throw new Error('feed request failed');
      return response.json();
    })
    .then(function (feed) {
      // Build DOM nodes instead of interpolating repo/source strings into HTML.
      var intro = document.createElement('p');
      intro.className = 'small';
      intro.textContent = 'Feed generated ' + (feed.generated_utc || 'date unknown') +
        ' by ' + (feed.generator || 'unknown generator') + '. ' +
        (feed.refresh_scope || '') + '. ' + (feed.policy || '');
      host.replaceChildren(intro);

      var table = document.createElement('table');
      var head = document.createElement('thead');
      var headerRow = document.createElement('tr');
      ['Source', 'Kind', 'Status', 'Detail', 'Checked / freshness'].forEach(function (label) {
        var th = document.createElement('th');
        th.textContent = label;
        headerRow.appendChild(th);
      });
      head.appendChild(headerRow);
      table.appendChild(head);

      var body = document.createElement('tbody');
      (feed.items || []).forEach(function (item) {
        var row = document.createElement('tr');
        var source = document.createElement('td');
        var anchor = document.createElement('a');
        try {
          var url = new URL(item.url || '', window.location.href);
          if (url.protocol === 'https:' || url.protocol === 'http:') {
            anchor.href = url.href;
            anchor.rel = 'noopener noreferrer';
            anchor.textContent = item.title || item.url || 'untitled source';
            source.appendChild(anchor);
          } else {
            source.textContent = item.title || item.url || 'untitled source';
          }
        } catch (error) {
          source.textContent = item.title || 'untitled source';
        }
        row.appendChild(source);

        [item.kind || 'unknown', item.status || 'status unknown', item.detail || '',
          [item.checked_utc || 'not timestamped', item.freshness || 'freshness unknown'].join(' · ')]
          .forEach(function (value, index) {
            var cell = document.createElement('td');
            if (index >= 2) cell.className = 'small';
            cell.textContent = value;
            row.appendChild(cell);
          });
        body.appendChild(row);
      });
      table.appendChild(body);
      host.appendChild(table);
    })
    .catch(function () {
      var message = document.createElement('p');
      message.className = 'small';
      message.textContent = 'Feed file unavailable. No freshness claim is made.';
      host.replaceChildren(message);
    });
})();
