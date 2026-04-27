/**
 * Page enhancements:
 *   1. Persist the active language in a cookie so the root '/' redirect
 *      (see build.py → root_html) lands on the user's last-chosen lang.
 *   2. Bottom-of-section "collapse" buttons — close the parent <details>
 *      and scroll back to its summary so the user isn't stranded mid-page.
 *      Handles both the legacy .phc-close (per-phase) and the new .fd-close
 *      (per-fuss).
 */
(function () {
  "use strict";

  // 1) Persist language: every page already declares <html lang="X"> — write it.
  var KNOWN = ["de", "en", "uk"];
  var pageLang = (document.documentElement.lang || "").toLowerCase();
  if (KNOWN.indexOf(pageLang) !== -1) {
    document.cookie =
      "lang=" + pageLang + ";max-age=31536000;path=/;samesite=lax";
  }

  // 2) Bottom collapse buttons. Each button declares which <details> it closes
  //    via the closest matching .{btn-class}-target ancestor.
  var COLLAPSE_RULES = [
    { button: ".phc-close", target: "details.phc-toggle" },
    { button: ".fd-close",  target: "details.fuss-details" }
  ];

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    for (var i = 0; i < COLLAPSE_RULES.length; i++) {
      var rule = COLLAPSE_RULES[i];
      var btn = t.closest(rule.button);
      if (!btn) continue;
      var details = btn.closest(rule.target);
      if (!details) return;
      details.open = false;
      var summary = details.querySelector(":scope > summary");
      if (summary && typeof summary.scrollIntoView === "function") {
        summary.scrollIntoView({
          block: "start",
          behavior: "instant" in (document.documentElement.style || {}) ? "instant" : "auto"
        });
      }
      return;
    }
  });
})();
