// nav.js — The Trading Journal
// Row 1: black utility bar — wordmark + tagline + right links
// Row 2: section tab bar — Overview / Trade Log / Education / Playbook / Strategies / Markets / Tools
(function () {
 var utility = document.getElementById('site-utility');
 if (utility) {
  utility.innerHTML = [
   '<nav class="top-bar">',
   ' <a href="/" class="top-wordmark">THE TRADING JOURNAL</a>',
   ' <span class="top-tagline">A daily log of trades, lessons, and probabilities</span>',
   ' <div class="top-links">',
   '  <a href="/about/">About</a>',
   '  <a href="/playbook/">Playbook</a>',
   '  <a href="/premium/">Premium</a>',
   '  <a href="/disclaimer/">Disclaimer</a>',
   ' </div>',
   '</nav>'
  ].join('\n');
 }

 var nav = document.getElementById('site-nav');
 if (nav) {
  nav.innerHTML = [
   '<div class="tab-bar">',
   ' <div class="tab-bar-inner">',
   '  <a href="/">Overview</a>',
   '  <a href="/trade-log/">Trade Log</a>',
   '  <a href="/education/">Education</a>',
   '  <a href="/playbook/">Playbook</a>',
   '  <a href="/strategies/">Strategies</a>',
   '  <a href="/markets/">Markets</a>',
   '  <a href="/tools/">Tools</a>',
   ' </div>',
   '</div>'
  ].join('\n');
 }

 var path = window.location.pathname;
 var tabs = document.querySelectorAll('.tab-bar a');
 tabs.forEach(function (tab) {
  var href = tab.getAttribute('href');
  if (href === path || (href !== '/' && path.startsWith(href))) {
   tab.classList.add('active');
  }
  if (href === '/' && (path === '/' || path === '/index')) {
   tab.classList.add('active');
  }
 });
})();
