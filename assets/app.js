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

  // 4) Timeline filter chips: «All» master ↔ per-entity slaves +
  //    per-variant marker visibility («highest-match» rule).
  //
  //    Each year-marker rect on the timeline is decomposed in the
  //    template into N divs — one per non-empty subset of its original
  //    entity set ({A,B,C} → A, B, C, AB, AC, BC, ABC). All variants
  //    share `[left, width]`; JS picks at most ONE to be visible per
  //    rect, the variant whose `data-ents` exactly equals the subset
  //    of `data-orig` that is currently checked among the filter chips.
  //
  //    Behaviour spec from user:
  //      - «All» chip is a pure UX master: it toggles every per-entity
  //        chip but does NOT drive marker visibility on its own.
  //      - When all per-entity chips are checked individually, «All»
  //        auto-checks; when any drops out, «All» auto-unchecks.
  //      - Of variants A, B, AB for a given rect, picking A+B shows AB
  //        only — the most specific match — never A or B alone.
  function syncTimelineFilters(scope) {
    var allBox = scope.querySelector('input[name="tl-filter-all"]');
    if (!allBox) return;
    var slaves = scope.querySelectorAll('input[name^="tl-filter-"]:not([name="tl-filter-all"])');
    if (!slaves.length) return;

    var tl = scope.closest(".tl") || scope.parentElement;

    function reflectAggregate() {
      var allChecked = true;
      for (var i = 0; i < slaves.length; i++) {
        if (!slaves[i].checked) { allChecked = false; break; }
      }
      // Don't fire change events here — direct property mutation only.
      allBox.checked = allChecked;
    }

    function checkedSet() {
      var s = {};
      for (var i = 0; i < slaves.length; i++) {
        if (!slaves[i].checked) continue;
        var m = slaves[i].name.match(/^tl-filter-(.+)$/);
        if (m && m[1] !== "all") s[m[1]] = true;
      }
      return s;
    }

    function refreshMarkers() {
      if (!tl) return;
      var checked = checkedSet();
      var markers = tl.querySelectorAll(".tl-coin-year");
      for (var i = 0; i < markers.length; i++) {
        var el = markers[i];
        var orig = (el.dataset.orig || "").split(",").filter(Boolean);
        var ents = (el.dataset.ents || "").split(",").filter(Boolean);
        // Compute checked ∩ orig and compare to this variant's ents.
        var hit = [];
        for (var j = 0; j < orig.length; j++) {
          if (checked[orig[j]]) hit.push(orig[j]);
        }
        // Both arrays were emitted alphabetically from Python — compare
        // by joined-string equality.
        var match = hit.length > 0 && hit.length === ents.length;
        if (match) {
          for (var k = 0; k < hit.length; k++) {
            if (hit[k] !== ents[k]) { match = false; break; }
          }
        }
        el.classList.toggle("tl-coin-year-show", match);
      }
    }

    allBox.addEventListener("change", function () {
      var v = allBox.checked;
      for (var i = 0; i < slaves.length; i++) slaves[i].checked = v;
      refreshMarkers();
    });
    for (var i = 0; i < slaves.length; i++) {
      slaves[i].addEventListener("change", function () {
        reflectAggregate();
        refreshMarkers();
      });
    }
    // Reflect / refresh once on load (in case the browser auto-restored
    // some state from a back/forward nav).
    reflectAggregate();
    refreshMarkers();
  }

  function initTimelineFilters() {
    var headers = document.querySelectorAll(".tl-header");
    for (var i = 0; i < headers.length; i++) syncTimelineFilters(headers[i]);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTimelineFilters);
  } else {
    initTimelineFilters();
  }

  // 5) Tooltip portal for elements inside `.mt-scroll`.
  //
  //    The CSS `[data-tooltip]:hover::after` rule positions the tooltip
  //    with `position: absolute` relative to the trigger. That works for
  //    most tooltips (timeline bars, filter chips), but inside the coin
  //    tables the surrounding `.mt-scroll` has `overflow-x: auto` (so
  //    narrow viewports get a horizontal scrollbar) which clips the
  //    tooltip on every side. `overflow-clip-margin-block` extends the
  //    vertical clip box but the horizontal axis is hard-capped by the
  //    scroll container.
  //
  //    Solution: for triggers within `.mt-scroll`, intercept hover and
  //    render a portal tooltip on `document.body` with `position: fixed`,
  //    sized and positioned via getBoundingClientRect. This bypasses ALL
  //    parent clipping. We only handle these specific triggers (not all
  //    `[data-tooltip]`) so timeline / chip tooltips keep their native
  //    CSS positioning, which is more performant and edge-anchored
  //    correctly for those elements.
  var portalEl = null;
  function ensurePortal() {
    if (portalEl) return portalEl;
    portalEl = document.createElement("div");
    portalEl.className = "tooltip-portal";
    portalEl.setAttribute("role", "tooltip");
    portalEl.style.cssText = [
      "position: fixed",
      "z-index: 1000",
      "pointer-events: none",
      "opacity: 0",
      "visibility: hidden"
    ].join(";");
    document.body.appendChild(portalEl);
    return portalEl;
  }
  function showPortal(trigger) {
    var text = trigger.getAttribute("data-tooltip");
    if (!text) return;
    var p = ensurePortal();
    p.textContent = text;
    p.style.visibility = "hidden";
    p.style.opacity = "0";
    // First measure with content laid out
    var rect = trigger.getBoundingClientRect();
    var tw = p.offsetWidth;
    var th = p.offsetHeight;
    var pad = 4;  // gap between trigger and tooltip
    // Default: above and centered on trigger
    var top = rect.top - th - pad;
    var left = rect.left + rect.width / 2 - tw / 2;
    // Flip below if there's not enough room above
    if (top < 4) top = rect.bottom + pad;
    // Clamp horizontally to viewport
    var vw = document.documentElement.clientWidth;
    if (left < 4) left = 4;
    if (left + tw > vw - 4) left = vw - tw - 4;
    p.style.top = top + "px";
    p.style.left = left + "px";
    p.style.visibility = "visible";
    p.style.opacity = "1";
  }
  function hidePortal() {
    if (!portalEl) return;
    portalEl.style.opacity = "0";
    portalEl.style.visibility = "hidden";
  }
  // Capture-phase delegation on document so we catch every hover into a
  // qualifying trigger, even if templates change shape later.
  document.addEventListener("mouseover", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    if (!t.closest(".mt-scroll")) return;
    showPortal(t);
  });
  document.addEventListener("mouseout", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    if (!t.closest(".mt-scroll")) return;
    // Only hide when the pointer actually leaves the trigger (not when it
    // moves to a child element of the same trigger).
    var related = ev.relatedTarget;
    if (related && t.contains(related)) return;
    hidePortal();
  });
  // Hide on scroll inside any scroll container (table or page) so a stale
  // tooltip doesn't drift away from its anchor while the user scrolls.
  document.addEventListener("scroll", hidePortal, true);
})();

/* ---------------------------------------------------------------------
 * Smart tooltip edge-anchoring (for non-portal `[data-tooltip]` ::after
 * pseudos — i.e. timeline layers, header chips, etc., everything OUTSIDE
 * the .mt-scroll table portal handler above).
 *
 * Default CSS centers the tooltip on its trigger (left:50% / translateX
 * (-50%)). For triggers near a viewport edge — common in the timeline
 * where layers near the right end have very little room on their right —
 * the centered tooltip overflows past the screen and gets clipped.
 *
 * Fix: on mouseover, measure the trigger's position vs viewport. If the
 * trigger's center is within ~half-tooltip-width of an edge, add a
 * `tt-anchor-left` or `tt-anchor-right` class. The corresponding CSS
 * (in styles.py) re-anchors the tooltip's left or right edge to the
 * trigger's edge instead of centering. On mouseout, the class is removed.
 * --------------------------------------------------------------------- */
(function () {
  "use strict";
  // Upper-bound estimate matching the CSS max-width: 320px → half = 160 px,
  // plus a small viewport-pad so the tooltip doesn't kiss the edge.
  var HALF_MAX = 160;
  var EDGE_PAD = 12;

  function classify(el) {
    var rect = el.getBoundingClientRect();
    var center = rect.left + rect.width / 2;
    var vw = document.documentElement.clientWidth || window.innerWidth;
    el.classList.remove("tt-anchor-left", "tt-anchor-right");
    if (center - HALF_MAX < EDGE_PAD) {
      el.classList.add("tt-anchor-left");
    } else if (center + HALF_MAX > vw - EDGE_PAD) {
      el.classList.add("tt-anchor-right");
    }
  }

  document.addEventListener("mouseover", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    // Skip table-cell tooltips — those use the portal system above.
    if (t.closest(".mt-scroll")) return;
    classify(t);
  });

  document.addEventListener("mouseout", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    if (t.closest(".mt-scroll")) return;
    var related = ev.relatedTarget;
    if (related && t.contains(related)) return;
    t.classList.remove("tt-anchor-left", "tt-anchor-right");
  });
})();
