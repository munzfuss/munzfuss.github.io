/**
 * Page enhancements:
 *   1. Persist the active language in a cookie so the root '/' redirect
 *      (see build.py → root_html) lands on the user's last-chosen lang.
 *   2. Bottom-of-section "collapse" buttons — close the parent <details>
 *      and scroll back to its summary so the user isn't stranded mid-page.
 *   3. Theme switcher (light v1 / dark v3). The inline <head> script
 *      already paints the stored theme before first render to avoid FOUC;
 *      this block reflects the active theme on the .theme-switch buttons
 *      and persists clicks back to localStorage.
 */

/* Tooltip table hydration (see scripts/lib/tooltip_dict.py): elements
   whose repeated tooltip text was moved into window.__TT carry
   `data-tt="<index>"`; restore `data-tooltip` on first hover / focus,
   in the capture phase so every later tooltip handler sees it. */
(function () {
  function hydrate(ev) {
    var el = ev.target;
    var tt = window.__TT;
    if (!tt || !el || !el.closest) return;
    for (el = el.closest("[data-tt]"); el; el = el.parentElement && el.parentElement.closest("[data-tt]")) {
      if (!el.hasAttribute("data-tooltip")) {
        var v = tt[+el.getAttribute("data-tt")];
        if (v != null) el.setAttribute("data-tooltip", v);
      }
    }
  }
  document.addEventListener("mouseover", hydrate, true);
  document.addEventListener("focusin", hydrate, true);
})();
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

  // 2a) Fold one phase: hide everything after its «.ph» header up to the next
  //     phase header / instrument block. Delegated, so it also works on the
  //     lazily fetched phase tables.
  document.addEventListener("click", function (ev) {
    var t = ev.target;
    var btn = t && t.closest ? t.closest(".ph-fold") : null;
    if (!btn) return;
    var head = btn.closest(".ph");
    if (!head) return;
    var fold = btn.getAttribute("aria-expanded") === "true";
    for (var el = head.nextElementSibling; el; el = el.nextElementSibling) {
      if (el.classList.contains("ph") || el.classList.contains("ph-inst")) break;
      el.classList.toggle("ph-folded", fold);
    }
    head.classList.toggle("ph-is-folded", fold);
    btn.setAttribute("aria-expanded", fold ? "false" : "true");
    btn.title = btn.getAttribute(fold ? "data-l-show" : "data-l-hide") || "";
  });

  // 2b) Lazy phase tables (see scripts/lib/lazy_fuss.py): on first open
  //     of a Müntzfuß block, fetch its `.fd-lazy[data-src]` fragment.
  function loadLazy(details) {
    var box = details.querySelector(":scope .fd-lazy[data-src]");
    if (!box) return Promise.resolve();
    if (box._lazyP) return box._lazyP;
    if (box.dataset.state) return Promise.resolve();
    box.dataset.state = "loading";
    box.innerHTML = '<div class="fd-lazy-msg">…</div>';
    box._lazyP = fetch(box.getAttribute("data-src"))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (txt) { box.innerHTML = txt; box.dataset.state = "done"; })
      .catch(function () {
        box.dataset.state = "";
        box._lazyP = null;
        box.innerHTML = '<div class="fd-lazy-msg">⚠ <a href="' +
          box.getAttribute("data-src") + '">' + box.getAttribute("data-src") + "</a></div>";
      });
    return box._lazyP;
  }
  document.addEventListener("toggle", function (ev) {
    var d = ev.target;
    if (d && d.matches && d.matches("details.fuss-details") && d.open) loadLazy(d);
  }, true);
  document.addEventListener("DOMContentLoaded", function () {
    var open = document.querySelectorAll("details.fuss-details[open]");
    for (var i = 0; i < open.length; i++) loadLazy(open[i]);
  });

  // 2c) Remember open Müntzfuß blocks and the scroll position across a
  //     reload (sessionStorage, per tab + page path). The browser's own
  //     scroll restoration runs before the lazy fragments exist, so it is
  //     switched off and the position is restored after they are inserted.
  (function () {
    var KEY = "mz-ui:" + location.pathname;
    var state = { open: [], y: 0, a: "", ao: 0 };
    var restoring = true;
    function read() {
      try { var v = JSON.parse(sessionStorage.getItem(KEY)); if (v && typeof v === "object") return v; }
      catch (e) {}
      return null;
    }
    function write() {
      if (restoring) return;
      try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
    }
    function collectOpen() {
      var out = [], ds = document.querySelectorAll("details.fuss-details[open]");
      for (var i = 0; i < ds.length; i++) out.push(ds[i].getAttribute("data-fuss"));
      return out;
    }
    function capture() {
      state.open = collectOpen();
      state.y = window.pageYOffset || document.documentElement.scrollTop || 0;
      var secs = document.querySelectorAll("section.fuss-block"), best = null, top = 0;
      for (var i = 0; i < secs.length; i++) {
        var t = secs[i].getBoundingClientRect().top;
        if (t <= 0) { best = secs[i]; top = t; } else break;
      }
      state.a = best ? best.id : "";
      state.ao = best ? -top : 0;
      write();
    }
    try { if ("scrollRestoration" in history) history.scrollRestoration = "manual"; } catch (e) {}

    var queued = false;
    window.addEventListener("scroll", function () {
      if (queued || restoring) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; capture(); });
    }, { passive: true });
    document.addEventListener("toggle", function (ev) {
      var d = ev.target;
      if (d && d.matches && d.matches("details.fuss-details")) capture();
    }, true);
    window.addEventListener("pagehide", function () { restoring = false; capture(); });

    function restoreScroll(saved) {
      var el = saved.a ? document.getElementById(saved.a) : null;
      var y = el
        ? el.getBoundingClientRect().top + (window.pageYOffset || 0) + (saved.ao || 0)
        : saved.y || 0;
      window.scrollTo(0, y);
    }
    function reveal() { document.documentElement.classList.remove("mz-restoring"); }
    function init() {
      var saved = read();
      var nav = (performance.getEntriesByType && performance.getEntriesByType("navigation")[0]) || {};
      var wanted = saved && (nav.type === "reload" || nav.type === "back_forward");
      if (!wanted) { restoring = false; reveal(); capture(); return; }
      var jobs = [];
      (saved.open || []).forEach(function (id) {
        var d = document.querySelector('details.fuss-details[data-fuss="' + id + '"]');
        if (!d) return;
        d.open = true;
        jobs.push(loadLazy(d));
      });
      Promise.all(jobs).then(function () {
        restoreScroll(saved);
        requestAnimationFrame(function () {
          restoreScroll(saved);
          restoring = false;
          reveal();
          capture();
        });
      });
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  })();

  // 3) Theme switcher.
  var THEMES = ["v1", "v3"];
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
    if (!theme || theme === currentTheme()) return;
    // Crossfade via the View Transitions API: the browser snapshots the old
    // page and fades it into the new theme on the GPU. Instant switch where
    // the API is missing or the user prefers reduced motion.
    var reduce = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (document.startViewTransition && !reduce) {
      document.startViewTransition(function () { applyTheme(theme); });
    } else {
      applyTheme(theme);
    }
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
  // Reading markers «(?)/(*)/(!)/(§)» carry a headline: when their reason has
  // more than one line, the first line is the short thesis and renders bold.
  // Built from text nodes, never innerHTML — tooltip text is data.
  // Every marker tooltip opens with a bold headline naming the marker kind;
  var MARK_HEAD = {
    uk: {template: "Шаблонне значення.", suspect: "Підозріле значення.", unverified: "Прогнозоване значення.", erroneous: "Помилкове значення."},
    de: {template: "Schablonenwert.", suspect: "Verdächtiger Wert.", unverified: "Geschätzter Wert.", erroneous: "Fehlerhafter Wert."},
    en: {template: "Template value.", suspect: "Suspect value.", unverified: "Estimated value.", erroneous: "Erroneous value."},
    da: {template: "Skabelonværdi.", suspect: "Mistænkelig værdi.", unverified: "Anslået værdi.", erroneous: "Fejlagtig værdi."}
  };
  function markKind(trigger) {
    var m = trigger && trigger.className &&
      /(?:^|\s)(suspect|erroneous|template)-mark(?:\s|$)|(?:^|\s)(unverified)(?:\s|$)/.exec(trigger.className);
    return m ? (m[1] || m[2]) : null;
  }
  function setTipText(box, text, trigger) {
    var kind = markKind(trigger);
    box.textContent = "";
    // Legend lines «{class}text» become colour chips (same palette as the Δ
    // badges); class is whitelisted and the text goes in as a text node.
    if (!kind && /(^|\n)\{(?:under-deep|under-mild|over-mild|over-strong)\}/.test(text)) {
      var lines = text.split("\n");
      var zone = null;
      for (var i = 0; i < lines.length; i++) {
        var m = /^\{(under-deep|under-mild|over-mild|over-strong)\}(.*)$/.exec(lines[i]);
        if (m) {
          if (!zone) {
            zone = document.createElement("div");
            zone.className = "tt-sd-zone";
            box.appendChild(zone);
          }
          var chip = document.createElement("span");
          chip.className = "tt-sd " + m[1];
          chip.textContent = m[2];
          zone.appendChild(chip);
        } else {
          zone = null;
          box.appendChild(document.createTextNode(lines[i]));
          if (i < lines.length - 1) box.appendChild(document.createTextNode("\n"));
        }
      }
      return;
    }
    if (!kind) { box.textContent = text; return; }
    var lang = (document.documentElement.lang || "en").slice(0, 2);
    var head = (MARK_HEAD[lang] || MARK_HEAD.en)[kind];
    if (head) {
      var h = document.createElement("b");
      h.textContent = head;
      box.appendChild(h);
      box.appendChild(document.createTextNode("\n"));
    }
    box.appendChild(document.createTextNode(text));
  }
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
  var portalFor = null;
  function showPortal(trigger) {
    // Moving between children of the same trigger must not re-fade.
    if (trigger === portalFor) return;
    portalFor = trigger;
    var text = trigger.getAttribute("data-tooltip");
    if (!text) return;
    var p = ensurePortal();
    setTipText(p, text, trigger);
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
    // Restart the CSS fade-in (tt-fade) on every new trigger.
    p.style.animation = "none";
    void p.offsetWidth;
    p.style.animation = "";
  }
  function hidePortal() {
    portalFor = null;
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
 * Act hover cards in the Grundwerte cards.
 *
 * A value line «per <act>» carries `<span class="gw-act" data-act="slug">`
 * and the act itself is a `.gw-row.gw-decree[data-act="slug"]` of the SAME
 * card. Hovering (or focusing / tapping) the reference shows that decree
 * row as a card: same markup, so the card CSS styles it; appended to <body>
 * because `.gw` clips overflow. The copy is built from cloned DOM only.
 *
 * A decree row may itself only say «per <other act>» (the 1524 Kongebrev
 * restates the 1514 Møntordning). Such a line is resolved: the phase whose
 * value is nothing but a reference is replaced by the referenced act's
 * phases (recursively, depth-capped; the schema forbids cycles), filtered
 * by label when the referring label lists parts («Pieces per mark / Rough
 * weight»). Citations (<sup>) are dropped — the card shows parameters.
 */
(function () {
  var pop = null, openFor = null;
  var MAX_DEPTH = 4;

  function ensurePop() {
    if (pop) return pop;
    pop = document.createElement("div");
    pop.className = "gw-act-pop";
    pop.id = "gw-act-pop";
    pop.setAttribute("role", "tooltip");
    pop.style.visibility = "hidden";
    pop.style.opacity = "0";
    document.body.appendChild(pop);
    return pop;
  }
  function decreeRow(card, slug) {
    var rows = card.querySelectorAll(".gw-row.gw-decree[data-act]");
    for (var i = 0; i < rows.length; i++) if (rows[i].getAttribute("data-act") === slug) return rows[i];
    return null;
  }
  function labelParts(label) {
    return label.toLowerCase().split("/").map(function (s) { return s.trim(); }).filter(Boolean);
  }
  function phaseLabel(ph) {
    var l = ph.querySelector(".gw-phase-label");
    return l ? l.textContent.trim() : "";
  }
  // A phase is a pure reference when, apart from its label and citations,
  // its only element child is one .gw-act and the text around it is short
  // connective («per», «згідно з», «iflg.»).
  function soleRef(ph) {
    var ref = null, text = "";
    for (var n = ph.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 3) { text += n.textContent; continue; }
      if (n.nodeType !== 1) continue;
      if (n.classList.contains("gw-phase-label") || n.tagName === "SUP") continue;
      if (n.classList.contains("gw-act") && !ref) { ref = n; continue; }
      return null;
    }
    if (!ref) return null;
    return text.trim().length <= 12 ? ref.getAttribute("data-act") : null;
  }
  // Resolved .gw-phase elements of an act: its own phases, with pure
  // reference lines replaced by the referenced act's phases.
  function phasesOf(card, slug, depth) {
    var row = decreeRow(card, slug);
    if (!row || depth > MAX_DEPTH) return [];
    var v = row.querySelector(".gw-v");
    if (!v) return [];
    var out = [];
    var phases = v.querySelectorAll(":scope > .gw-phase");
    for (var i = 0; i < phases.length; i++) {
      var ph = phases[i];
      var target = soleRef(ph);
      if (target && target !== slug) {
        var parts = labelParts(phaseLabel(ph));
        var got = phasesOf(card, target, depth + 1);
        var pick = got;
        if (parts.length > 1) {
          pick = got.filter(function (g) { return parts.indexOf(phaseLabel(g).toLowerCase()) >= 0; });
          if (!pick.length) pick = got;
        }
        for (var j = 0; j < pick.length; j++) out.push(pick[j]);
      } else {
        out.push(ph.cloneNode(true));
      }
    }
    return out;
  }
  function buildActCard(card, slug) {
    var row = decreeRow(card, slug);
    if (!row) return null;
    var box = document.createElement("div");
    box.className = "gw-rows";
    var r = document.createElement("div");
    r.className = "gw-row gw-decree";
    var k = row.querySelector(".gw-k");
    if (k) r.appendChild(k.cloneNode(true));
    var v = document.createElement("div");
    v.className = "gw-v";
    var phases = phasesOf(card, slug, 0);
    for (var i = 0; i < phases.length; i++) v.appendChild(phases[i]);
    r.appendChild(v);
    box.appendChild(r);
    // parameters only: no citations, no nested hover targets, no ids
    var strip = box.querySelectorAll("sup");
    for (i = 0; i < strip.length; i++) strip[i].parentNode.removeChild(strip[i]);
    var acts = box.querySelectorAll(".gw-act");
    for (i = 0; i < acts.length; i++) { acts[i].removeAttribute("data-act"); acts[i].removeAttribute("tabindex"); }
    var ids = box.querySelectorAll("[id]");
    for (i = 0; i < ids.length; i++) ids[i].removeAttribute("id");
    return box;
  }
  function show(trigger) {
    if (trigger === openFor) return;
    hide();
    var card = trigger.closest(".gw");
    var slug = trigger.getAttribute("data-act");
    if (!card || !slug) return;
    var content = buildActCard(card, slug);
    if (!content) return;
    var p = ensurePop();
    p.textContent = "";
    p.appendChild(content);
    openFor = trigger;
    trigger.classList.add("gw-act-open");
    trigger.setAttribute("aria-describedby", p.id);
    var rect = trigger.getBoundingClientRect();
    var tw = p.offsetWidth, th = p.offsetHeight, pad = 8;
    var top = rect.top - th - pad;
    if (top < 4) top = rect.bottom + pad;
    var vw = document.documentElement.clientWidth;
    var left = rect.left + rect.width / 2 - tw / 2;
    if (left + tw > vw - 4) left = vw - tw - 4;
    if (left < 4) left = 4;
    p.style.top = top + "px";
    p.style.left = left + "px";
    p.style.visibility = "visible";
    p.style.opacity = "1";
    p.style.animation = "none";
    void p.offsetWidth;
    p.style.animation = "";
  }
  function hide() {
    if (openFor) {
      openFor.classList.remove("gw-act-open");
      openFor.removeAttribute("aria-describedby");
    }
    openFor = null;
    if (!pop) return;
    pop.style.opacity = "0";
    pop.style.visibility = "hidden";
  }
  function triggerOf(ev) {
    var t = ev.target && ev.target.closest && ev.target.closest(".gw-act[data-act]");
    return t && !t.closest(".gw-act-pop") ? t : null;
  }
  var acts = document.querySelectorAll(".gw .gw-act[data-act]");
  for (var i = 0; i < acts.length; i++) acts[i].setAttribute("tabindex", "0");
  // Without hover (touch) the tap is the only control: a tap on the
  // reference toggles the card, a tap anywhere else closes it. A touch
  // browser emulates hover on the first tap — mouseover and focusin would
  // open the card and the click that follows would close it again, so the
  // reference needed two taps. Hover / focus handlers are therefore skipped
  // on such devices; with a pointer the card follows hover and a click on
  // the trigger is left alone (it would close the card under the cursor).
  var noHover = window.matchMedia && window.matchMedia("(hover: none)").matches;
  document.addEventListener("mouseover", function (ev) { if (noHover) return; var t = triggerOf(ev); if (t) show(t); });
  document.addEventListener("mouseout", function (ev) {
    if (noHover) return;
    var t = triggerOf(ev);
    if (!t || t !== openFor) return;
    if (ev.relatedTarget && t.contains(ev.relatedTarget)) return;
    hide();
  });
  document.addEventListener("focusin", function (ev) { if (noHover) return; var t = triggerOf(ev); if (t) show(t); });
  document.addEventListener("focusout", function (ev) { if (noHover) return; var t = triggerOf(ev); if (t && t === openFor) hide(); });
  document.addEventListener("click", function (ev) {
    var t = triggerOf(ev);
    if (t) { if (noHover) { if (t === openFor) hide(); else show(t); } return; }
    if (openFor) hide();
  });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") hide(); });
  document.addEventListener("scroll", hide, true);
  window.addEventListener("resize", hide);
})();

/* ---------------------------------------------------------------------
 * Smart tooltip edge-anchoring (for non-portal `[data-tooltip]` ::after
 * pseudos — i.e. timeline layers, header chips, etc., everything OUTSIDE
 * the .mt-scroll table portal handler above).
 *
 * Default CSS centers the tooltip on its trigger (left:50% / translateX
 * (-50%)); hover zones centre it on the bar's cumulative band (`--tt-cx`).
 * For triggers near a viewport edge — the whole timeline on a phone, the
 * right end of a bar on any screen — the centered tooltip overflows past
 * the screen and gets clipped.
 *
 * Fix: on mouseover, compute where the centered box WOULD land (intended
 * centre − half the fitted width), clamp that to the viewport minus a
 * pad, and hand the result to CSS as `--tt-left` (px, relative to the
 * trigger's left edge) under the class `tt-anchor-px`. The CSS rule
 * (style.base.css) then pins the box at that offset instead of centring.
 * Pixel placement, not a left/right class, because the hover-zone rule
 * has the same specificity as a class variant and used to win: on a
 * phone the zone tooltips ran off the left edge (2026-10-13).
 * On mouseout, the class is removed.
 * --------------------------------------------------------------------- */
(function () {
  "use strict";
  var EDGE_PAD = 12;        // viewport pad so the tooltip doesn't kiss the edge
  var MAX_W = 320;          // matches CSS max-width
  var H_PAD = 20;           // 10 px × 2 horizontal tooltip padding
  var FIT_BUFFER = 1;       // 1 px sub-pixel safety

  function viewportWidth() {
    return document.documentElement.clientWidth || window.innerWidth;
  }
  // The widest box the viewport can hold with the pad on both sides.
  function maxWidth() {
    return Math.max(80, Math.min(MAX_W, viewportWidth() - 2 * EDGE_PAD));
  }

  function classify(el) {
    var rect = el.getBoundingClientRect();
    var vw = viewportWidth();
    // Intended centre: hover zones anchor at the band centre (`--tt-cx`,
    // a percentage of the zone, set inline by the template); everything
    // else at the trigger's own centre.
    var cxPct = parseFloat(el.style.getPropertyValue("--tt-cx"));
    var center = rect.left + rect.width * (isNaN(cxPct) ? 0.5 : cxPct / 100);
    var w = parseFloat(el.style.getPropertyValue("--tt-w"));
    if (isNaN(w) || !w) w = maxWidth();
    var left = center - w / 2;
    var maxLeft = vw - EDGE_PAD - w;
    if (left > maxLeft) left = maxLeft;
    if (left < EDGE_PAD) left = EDGE_PAD;
    el.style.setProperty("--tt-left", (left - rect.left) + "px");
    el.classList.add("tt-anchor-px");
  }

  // Off-screen measurement element. Mirrors the tooltip's text styling
  // and width constraints so the browser wraps text identically. We then
  // walk Range.getClientRects() to find the longest wrapped line and set
  // `--tt-w` on the trigger so the actual tooltip box shrinks to match.
  // Without this fix the box stays at max-width=320px even when the
  // longest line is 240 px wide, leaving visible whitespace on the right.
  var measEl = null;
  function getMeasEl() {
    if (measEl) return measEl;
    measEl = document.createElement("div");
    measEl.style.cssText = (
      "position:absolute;visibility:hidden;pointer-events:none;" +
      "top:0;left:-99999px;" +
      "padding:6px 10px;" +
      "font-family:var(--font-body);font-size:11.5px;" +
      "font-weight:400;letter-spacing:0;text-transform:none;" +
      "line-height:1.45;" +
      "white-space:pre-line;" +
      "width:max-content;"
    );
    document.body.appendChild(measEl);
    return measEl;
  }

  function fit(el) {
    var text = el.getAttribute("data-tooltip");
    if (!text) return;
    var m = getMeasEl();
    m.style.maxWidth = maxWidth() + "px";
    m.textContent = text;
    var range = document.createRange();
    try {
      range.selectNodeContents(m);
    } catch (e) {
      return;
    }
    var rects = range.getClientRects();
    var maxLine = 0;
    for (var i = 0; i < rects.length; i++) {
      if (rects[i].width > maxLine) maxLine = rects[i].width;
    }
    if (!maxLine) return;
    var fitted = Math.ceil(maxLine + H_PAD + FIT_BUFFER);
    var cap = maxWidth();
    if (fitted > cap) fitted = cap;
    el.style.setProperty("--tt-w", fitted + "px");
  }

  document.addEventListener("mouseover", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    // Skip table-cell tooltips — those use the portal system above.
    if (t.closest(".mt-scroll")) return;
    fit(t);
    // Zones of one bar share a width (below); settle it before placing.
    if (t.classList.contains("tl-bar-hover-zone")) unifyZoneWidths(t);
    classify(t);
  });

  document.addEventListener("mouseout", function (ev) {
    var t = ev.target && ev.target.closest && ev.target.closest("[data-tooltip]");
    if (!t) return;
    if (t.closest(".mt-scroll")) return;
    var related = ev.relatedTarget;
    if (related && t.contains(related)) return;
    t.classList.remove("tt-anchor-px");
  });

  // ------------------------------------------------------------------
  // Width unification across hover zones inside the same `.tl-bar-layers`.
  //
  // Each `.tl-bar-hover-zone` carries a different `data-tooltip` (active
  // layer set differs by zone), so the per-trigger `fit()` above would
  // give each zone its own width — the tooltip would change size as
  // the cursor crossed zone boundaries. To keep the box visually
  // stable, on first hover into any zone of a bar we measure ALL the
  // bar's zones, find the widest fitted width, and apply it to every
  // sibling via the same `--tt-w` CSS variable that `fit()` sets.
  // ------------------------------------------------------------------
  function unifyZoneWidths(zone) {
    var wrap = zone.closest(".tl-bar-layers");
    if (!wrap || wrap.dataset.zonesFitted === "1") return;
    var zones = wrap.querySelectorAll(".tl-bar-hover-zone");
    if (!zones.length) return;
    var maxW = 0;
    for (var i = 0; i < zones.length; i++) {
      // Reuse fit()'s measurement loop by temporarily letting each
      // sibling compute its own --tt-w, then take the max.
      fit(zones[i]);
      var w = parseFloat(zones[i].style.getPropertyValue("--tt-w"));
      if (!isNaN(w) && w > maxW) maxW = w;
    }
    if (!maxW) return;
    var unified = maxW + "px";
    for (var j = 0; j < zones.length; j++) {
      zones[j].style.setProperty("--tt-w", unified);
    }
    wrap.dataset.zonesFitted = "1";
  }


  /* ------------------------------------------------------------------ *
   *  Back-to-top button                                                 *
   *                                                                     *
   *  Injected via JS (no template change). Appears once the user has    *
   *  scrolled past max(viewport-height, 15 % of page height). Click     *
   *  triggers a fast smooth scroll to the top. Throttled via rAF.       *
   *                                                                     *
   *  The threshold matches the user's spec:                             *
   *    «max(1 екран по висоті, 15 % всього скрола чи сторінки)»         *
   *  Computed lazily on each scroll event because page height can       *
   *  change (e.g. <details> expansions, lazy-loaded content).           *
   * ------------------------------------------------------------------ */
  (function () {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btt-button";
    btn.setAttribute("aria-label", "Scroll to top");
    btn.setAttribute("title", "Scroll to top");
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<polyline points="6 14 12 8 18 14"></polyline>' +
      "</svg>";
    document.body.appendChild(btn);

    var prefersReducedMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* Compute the show-threshold: max(viewport-height, 15% of page height). */
    function threshold() {
      var viewportH = window.innerHeight || document.documentElement.clientHeight;
      var pageH = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.offsetHeight
      );
      return Math.max(viewportH, pageH * 0.15);
    }

    var ticking = false;
    function update() {
      ticking = false;
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      if (y > threshold()) {
        btn.classList.add("is-visible");
      } else {
        btn.classList.remove("is-visible");
      }
    }
    function onScroll() {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(update);
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    update();

    /* Fast smooth-scroll to top. Browser's behavior:'smooth' implementation
       gets sluggish on very long pages — implement a custom ease-out animation
       with a capped duration so the visual is always quick. */
    function scrollToTop() {
      var startY = window.pageYOffset || document.documentElement.scrollTop || 0;
      if (startY <= 0) return;

      if (prefersReducedMotion) {
        window.scrollTo(0, 0);
        return;
      }

      /* Duration scales mildly with distance — long pages don't ALL get
         capped at one fixed time (feels disconnected on huge scrolls),
         but the scaling is sub-linear: 600 ms for 4 viewports, 900 ms
         for 16 viewports. Hard cap at 900 ms. */
      var viewportH = window.innerHeight || 800;
      var viewports = startY / viewportH;
      var duration = Math.min(900, 300 + 150 * Math.sqrt(viewports));

      var t0 = performance.now();
      function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }
      function step(now) {
        var elapsed = now - t0;
        var k = Math.min(1, elapsed / duration);
        var y = startY * (1 - easeOutCubic(k));
        window.scrollTo(0, y);
        if (k < 1) window.requestAnimationFrame(step);
      }
      window.requestAnimationFrame(step);
    }
    btn.addEventListener("click", scrollToTop);
  })();
})();
