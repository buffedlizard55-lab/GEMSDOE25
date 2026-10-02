// copy-to-clipboard for any element with data-copy-target; renders the optional feed.
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
(function () {
  var host = document.getElementById('feed');
  if (!host) return;
  var base = host.getAttribute('data-base') || '';
  fetch(base + 'data/feed.json', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (f) {
    var h = '<p class="small">Feed generated <b>' + f.generated_utc + '</b> by <code>' + f.generator + '</code>. ' + f.policy + '</p><table><thead><tr><th>Source</th><th>Status</th><th>Detail</th></tr></thead><tbody>';
    f.items.forEach(function (i) { h += '<tr><td><a href="' + i.url + '">' + i.title + '</a></td><td>' + i.status + '</td><td class="small">' + (i.detail || '') + '</td></tr>'; });
    host.innerHTML = h + '</tbody></table>';
  }).catch(function () { host.innerHTML = '<p class="small">Feed file not found or not yet generated.</p>'; });
})();
