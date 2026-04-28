/**
 * Page enhancements:
 *   1. Persist the active language in a cookie so the root '/' redirect
 *      (see build.py → root_html) lands on the user's last-chosen lang.
 *   2. Bottom-of-section "collapse" buttons — close the parent <details>
 *      and scroll back to its summary so the user isn't stranded mid-page.
 *   3. Theme switcher (Atlas / Codex / Noir). The inline <head> script
 *      already paints the stored theme before first render to avoid FOUC;
 *      this block reflects the active theme on the .theme-switch buttons
 *      and persists clicks back to localStorage.
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

  // 2) Bottom collapse buttons.
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

  // 3) Theme switcher.
  var THEMES = ["v1", "v2", "v3"];
  function currentTheme() {
    var t = document.documentElement.dataset.theme || "";
    return THEMES.indexOf(t) >= 0 ? t : "v3";
  }
  function applyTheme(t) {
    if (THEMES.indexOf(t) < 0) return;
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem("mz-theme", t); } catch (e) {}
    reflectActive(t);
  }
  function reflectActive(t) {
    var btns = document.querySelectorAll(".theme-switch .th");
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      var matches = b.dataset && b.dataset.theme === t;
      b.classList.toggle("active", !!matches);
      b.setAttribute("aria-pressed", matches ? "true" : "false");
    }
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest(".theme-switch .th");
    if (!t) return;
    var theme = t.dataset && t.dataset.theme;
    if (theme) applyTheme(theme);
  });

  // Reflect the current (inline-script-applied) theme on first paint.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { reflectActive(currentTheme()); });
  } else {
    reflectActive(currentTheme());
  }
})();
