// footer.js — The Trading Journal
(function () {
 function populateFooter() {
  var footer = document.getElementById('site-footer');
  if (!footer) return;
  if (footer.innerHTML.trim() !== '') return;
  footer.innerHTML = [
   '<div class="main-footer">',
   ' <div class="footer-grid">',
   '  <div class="footer-brand">',
   '   <h4>The Trading Journal</h4>',
   '   <p>A working journal of SPX/XSP options trades — entry reasoning, position structure, and P&amp;L. '
   +    'Built on the math of risk vs reward, market probabilities, and a written playbook.</p>',
   '  </div>',
   '  <div class="footer-nav">',
   '   <h5>Journal</h5>',
   '   <ul>',
   '    <li><a href="/trade-log/">Trade Log</a></li>',
   '    <li><a href="/forecasts/">Forecasts</a></li>',
   '    <li><a href="/playbook/">Playbook</a></li>',
   '    <li><a href="/strategies/">Strategies</a></li>',
   '   </ul>',
   '  </div>',
   '  <div class="footer-nav">',
   '   <h5>Learn</h5>',
   '   <ul>',
   '    <li><a href="/education/">Education</a></li>',
   '    <li><a href="/markets/">Markets (SPX, XSP, Sectors)</a></li>',
   '    <li><a href="/tools/">Tools &amp; Affiliates</a></li>',
   '   </ul>',
   '  </div>',
   '  <div class="footer-nav">',
   '   <h5>Company</h5>',
   '   <ul>',
   '    <li><a href="/about/">About</a></li>',
   '    <li><a href="/premium/">Premium (Coming Soon)</a></li>',
   '    <li><a href="/contact/">Contact</a></li>',
   '   </ul>',
   '  </div>',
   '  <div class="footer-nav">',
   '   <h5>Legal</h5>',
   '   <ul>',
   '    <li><a href="/disclaimer/">Investment Disclaimer</a></li>',
   '    <li><a href="/privacy/">Privacy Policy</a></li>',
   '    <li><a href="/terms/">Terms of Use</a></li>',
   '   </ul>',
   '  </div>',
   ' </div>',
   ' <div class="footer-bottom">',
   '  <p>&copy; 2026 The Trading Journal. All rights reserved. Operated by Bacotti Enterprises.</p>',
   '  <p><strong>Not investment advice.</strong> The content on this site is for informational and educational purposes only. '
   +    'Options trading involves substantial risk of loss. Past performance does not guarantee future results. '
   +    'You are solely responsible for your own investment decisions. See the <a href="/disclaimer/">full disclaimer</a>.</p>',
   ' </div>',
   '</div>'
  ].join('\n');
 }

 if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', populateFooter);
 } else {
  populateFooter();
 }
 window.addEventListener('load', populateFooter);
})();
