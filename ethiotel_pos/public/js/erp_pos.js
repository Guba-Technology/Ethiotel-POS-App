/**
 * Ethio Telecom — Frappe Desk Theme Enhancer
 * ============================================
 * Injects Ethio Telecom brand colours into the Frappe v15 desk.
 * Uses [data-theme]-prefixed CSS to win specificity against Frappe's
 * bundled SCSS. Also handles POSAwesome Vuetify theme override.
 */

(function () {
  "use strict";

  /* ==================================================================
     SET FRAPPE THEME VARIABLES DIRECTLY ON <html>
     Frappe v15 applies its theme as inline styles on documentElement,
     which beat any CSS rule.  We must set them via JS with 'important'
     priority so they survive Frappe's own theme re-apply.
     ================================================================== */
  function setThemeVars() {
    var root = document.documentElement;
    if (!root) return;

    var vars = {
      "--primary": "#8DC63F",
      "--primary-color": "#8DC63F",
      "--primary-light": "#F3F9EB",
      "--btn-primary-bg": "#8DC63F",
      "--btn-primary": "#72A130",

      "--bg-color": "#F0F3F6",
      "--fg-color": "#FFFFFF",
      "--card-bg": "#FFFFFF",
      "--bg-light-gray": "#F6F8FA",
      "--bg-gray": "#EDF1F4",

      "--text-color": "#1A1F24",
      "--text-muted": "#6B7A86",
      "--text-light": "#9AABB5",
      "--heading-color": "#1A1F24",

      "--navbar-bg": "#8DC63F",
      "--navbar-color": "#FFFFFF",

      "--sidebar-bg": "#FFFFFF",
      "--sidebar-color": "#1A1F24",
      "--sidebar-select-color": "#F3F9EB",
      "--sidebar-hover-color": "#EDF1F4",
      "--sidebar-border-color": "#E2E8ED",

      "--border-color": "#E2E8ED",
      "--border-radius": "6px",
      "--border-radius-sm": "4px",
      "--border-radius-md": "12px",

      "--control-bg": "#F6F8FA",
      "--control-bg-on-gray": "#EDF1F4",
      "--awesome-bar-bg": "#F6F8FA",

      "--error-bg": "#FDE7E8",
      "--error-color": "#ED1C24",
      "--success-bg": "#E5F7EE",
      "--success-color": "#00965E",
      "--warning-bg": "#FFF9E5",
      "--warning-color": "#7A5A00",
      "--info-bg": "#E0F3FF",
      "--info-color": "#004370",

      "--shadow-base": "0 1px 2px rgba(26,31,36,.04)",
      "--shadow-sm": "0 1px 3px rgba(26,31,36,.06)",
      "--shadow-md": "0 4px 12px rgba(26,31,36,.06)",
      "--shadow-lg": "0 12px 40px rgba(26,31,36,.10)",
    };

    Object.keys(vars).forEach(function (key) {
      root.style.setProperty(key, vars[key], "important");
    });

  }

  /* ==================================================================
     INJECT HIGH-SPECIFICITY CSS FOR [data-theme] WINS
     Frappe's bundled SCSS uses [data-theme="light"] selectors that
     beat plain class rules.  We inject after Frappe's bundle.
     ================================================================== */
  function injectHighSpecCSS() {
    var id = "et-high-spec";
    if (document.getElementById(id)) return;

    var style = document.createElement("style");
    style.id = id;
    style.textContent = [
      /* --- Frappe primary colour (belt-and-suspenders) --- */
      "[data-theme] {",
      "  --primary: #8DC63F !important;",
      "  --primary-color: #8DC63F !important;",
      "  --primary-light: #F3F9EB !important;",
      "  --btn-primary-bg: #8DC63F !important;",
      "  --bg-color: #F0F3F6 !important;",
      "  --fg-color: #FFFFFF !important;",
      "}",

      /* --- Sidebar selected state --- */
      "[data-theme] .sidebar-item-container.selected > .sidebar-item {",
      "  background: #F3F9EB !important;",
      "  border-left: none !important;",
      "  color: #567A24 !important;",
      "  box-shadow: inset 0 0 0 1px rgba(141,198,63,.2) !important;",
      "}",

      /* --- Buttons --- */
      "[data-theme] .btn-primary {",
      "  background: #8DC63F !important;",
      "  border-color: #8DC63F !important;",
      "  color: #fff !important;",
      "  box-shadow: 0 2px 6px rgba(141,198,63,.25) !important;",
      "}",

      "[data-theme] .btn-primary:hover {",
      "  background: #72A130 !important;",
      "}",

      /* --- Form controls focus --- */
      "[data-theme] .form-control:focus,",
      "[data-theme] .input-with-feedback:focus {",
      "  border-color: #8DC63F !important;",
      "  box-shadow: 0 0 0 3px rgba(141,198,63,.15) !important;",
      "}",

      /* --- Awesome bar input on green navbar --- */
      '[data-theme] .search-bar .awesomplete input {',
      "  background: #fff !important;",
      "  border: 1px solid rgba(255,255,255,.3) !important;",
      "  min-height: 36px !important;",
      "}",
      '[data-theme] .search-bar .awesomplete input:focus {',
      "  border-color: #72A130 !important;",
      "  box-shadow: 0 0 0 3px rgba(255,255,255,.2) !important;",
      "}",

      /* --- Awesome bar dropdown --- */
      "[data-theme] .awesomplete > ul {",
      "  background: #ffffff !important;",
      "  border: 1px solid #E2E8ED !important;",
      "  border-radius: 12px !important;",
      "  box-shadow: 0 12px 40px rgba(26,31,36,.10) !important;",
      "  padding: 6px !important;",
      "}",

      "[data-theme] .awesomplete > ul > li {",
      "  color: #1A1F24 !important;",
      "  background: transparent !important;",
      "  border-radius: 6px !important;",
      "  padding: 8px 14px !important;",
      "  font-size: 13px !important;",
      "  cursor: pointer !important;",
      "}",

      "[data-theme] .awesomplete > ul > li a,",
      "[data-theme] .awesomplete > ul > li .awesomplete-item,",
      "[data-theme] .awesomplete > ul > li .awesomplete-item strong,",
      "[data-theme] .awesomplete > ul > li .awesomplete-item span {",
      "  color: #1A1F24 !important;",
      "  text-decoration: none !important;",
      "}",

      "[data-theme] .awesomplete > ul > li:hover,",
      "[data-theme] .awesomplete > ul > li[aria-selected=\"true\"] {",
      "  background: #F3F9EB !important;",
      "  color: #567A24 !important;",
      "}",

      "[data-theme] .awesomplete > ul > li:hover a,",
      "[data-theme] .awesomplete > ul > li[aria-selected=\"true\"] a {",
      "  color: #567A24 !important;",
      "}",

      "[data-theme] .awesomplete > ul > li .awesomplete-item-description {",
      "  color: #6B7A86 !important;",
      "  font-size: 11px !important;",
      "}",

      /* --- Navbar — Ethio Telecom green --- */
      "[data-theme] .navbar {",
      "  background: #8DC63F !important;",
      "  box-shadow: 0 2px 8px rgba(141,198,63,.25) !important;",
      "  border-bottom: none !important;",
      "}",
      "[data-theme] .navbar .navbar-brand,",
      "[data-theme] .navbar .app-name {",
      "  color: #fff !important;",
      "}",
      "[data-theme] .navbar a, [data-theme] .navbar .icon {",
      "  color: rgba(255,255,255,.8) !important;",
      "}",

      /* --- Checkbox --- */
      "[data-theme] .list-row-checkbox {",
      "  accent-color: #8DC63F !important;",
      "}",

      /* --- Alerts --- */
      "[data-theme] .alert-primary { background: #F3F9EB !important; color: #567A24 !important; border-left: 3px solid #8DC63F !important; }",
      "[data-theme] .alert-danger  { background: #FDE7E8 !important; color: #ED1C24 !important; border-left: 3px solid #ED1C24 !important; }",
      "[data-theme] .alert-success { background: #E5F7EE !important; color: #00965E !important; border-left: 3px solid #00965E !important; }",
      "[data-theme] .alert-warning { background: #FFF9E5 !important; color: #7A5A00 !important; border-left: 3px solid #FFC20E !important; }",

      /* --- Pagination active --- */
      "[data-theme] .pagination > li.active > a,",
      "[data-theme] .pagination > li.active > span {",
      "  background: #8DC63F !important;",
      "  border-color: #8DC63F !important;",
      "  color: #fff !important;",
      "}",

      /* --- Progress bar --- */
      "[data-theme] .progress-bar {",
      "  background: linear-gradient(90deg, #8DC63F, #0072BC) !important;",
      "}",

      /* --- POSAwesome Vuetify overrides (scoped to posapp route) --- */
      '[data-theme] body[data-page-route="posapp"] {',
      "  --v-theme-primary: 141, 198, 63 !important;",
      "  --v-theme-secondary: 0, 114, 188 !important;",
      "  --v-theme-accent: 255, 194, 14 !important;",
      "  --v-theme-success: 0, 150, 94 !important;",
      "  --pos-primary: #8DC63F !important;",
      "  --pos-secondary: #0072BC !important;",
      "  --pos-accent: #FFC20E !important;",
      "}",

      '[data-theme] .posapp .v-btn--color-primary {',
      "  background-color: #8DC63F !important;",
      "  color: #fff !important;",
      "}",

      '[data-theme] .posapp .v-btn--color-secondary {',
      "  background-color: #0072BC !important;",
      "  color: #fff !important;",
      "}",
    ].join("\n");
    document.head.appendChild(style);
  }

  /* ==================================================================
     BRAND THE WORKSPACE TITLES
     ================================================================== */
  function brandTitles() {
    var brand = document.querySelector(".navbar .navbar-brand");
    if (brand && !brand.dataset.etSet) {
      var txt = brand.querySelector(".app-name, span");
      if (txt) txt.textContent = "Ethio Telecom";
      brand.dataset.etSet = "1";
    }
  }

  /* ==================================================================
     STAGGERED CARD REVEAL (workspace widgets)
     ================================================================== */
  var REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function stagger() {
    if (REDUCE) return;
    var cards = Array.from(
      document.querySelectorAll(".widget-group .widget, .shortcut-widget-box")
    ).filter(function (c) { return !c.dataset.etReveal && c.offsetParent !== null; });

    cards.forEach(function (card, i) {
      card.dataset.etReveal = "1";
      card.style.opacity = "0";
      card.style.transform = "translateY(8px)";
      card.style.transition = "opacity 260ms ease, transform 260ms cubic-bezier(.25,.46,.45,.94)";
      setTimeout(function () {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      }, 30 * i);
    });
  }

  /* ==================================================================
     BUTTON RIPPLE EFFECT
     ================================================================== */
  function ripple() {
    if (REDUCE) return;
    document.addEventListener("click", function (e) {
      var btn = e.target.closest(".btn");
      if (!btn) return;
      var rect = btn.getBoundingClientRect();
      var r = document.createElement("span");
      var size = Math.max(rect.width, rect.height);
      Object.assign(r.style, {
        position: "absolute",
        width: size + "px",
        height: size + "px",
        left: e.clientX - rect.left - size / 2 + "px",
        top: e.clientY - rect.top - size / 2 + "px",
        borderRadius: "50%",
        background: "rgba(255,255,255,0.3)",
        pointerEvents: "none",
        transform: "scale(0)",
        transition: "transform 400ms ease, opacity 400ms ease",
      });
      if (getComputedStyle(btn).position === "static") btn.style.position = "relative";
      btn.style.overflow = "hidden";
      btn.appendChild(r);
      requestAnimationFrame(function () {
        r.style.transform = "scale(1.5)";
        r.style.opacity = "0";
      });
      setTimeout(function () { r.remove(); }, 450);
    });
  }

  /* ==================================================================
     INIT
     ================================================================== */
  function init() {
    setThemeVars();
    brandTitles();
    stagger();
  }

  /* ==================================================================
     BOOT
     ================================================================== */
  function boot() {
    setThemeVars();
    injectHighSpecCSS();
    init();
    ripple();

    // Re-apply theme vars periodically because Frappe's frappe.ui.set_theme()
    // runs after AJAX calls and can override our inline styles.
    setInterval(setThemeVars, 2000);

    // Re-init on Frappe route changes
    if (typeof frappe !== "undefined") {
      if (frappe.router) {
        frappe.router.on("change", function () {
          setTimeout(init, 240);
        });
      }
      if (frappe.after_ajax) {
        frappe.after_ajax(function () { setTimeout(init, 100); });
      }
    }

    // DOM observer for dynamic content
    var mo = new MutationObserver(function () {
      init();
    });
    if (document.body) {
      mo.observe(document.body, { childList: true, subtree: true });
    }

    console.log(
      "%cEthio Telecom Desk Theme — Active",
      "color:#8DC63F;font-weight:700;font-size:13px"
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
