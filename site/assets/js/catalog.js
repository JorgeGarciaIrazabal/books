/* Catalog page behavior: language filter chips, text search, an accessible
   results count, and a visible empty state with a one-tap reset. The book
   cards themselves are static HTML, so the full catalog remains available
   without JavaScript. */
(function () {
  "use strict";

  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var search = document.getElementById("search");
  var books = Array.prototype.slice.call(document.querySelectorAll(".book"));
  var status = document.getElementById("results-status");
  var emptyState = document.getElementById("empty-state");
  var clearButton = document.getElementById("clear-filters");

  if (!books.length) { return; }

  var state = { lang: "all", q: "" };

  var params = new URLSearchParams(window.location.search);
  var preset = params.get("lang");
  if (preset === "en" || preset === "es") { state.lang = preset; }

  function apply() {
    var shown = 0;
    var total = books.length;
    books.forEach(function (card) {
      var okLang = state.lang === "all" || card.getAttribute("data-language") === state.lang;
      var haystack = (card.getAttribute("data-search") || "").toLowerCase();
      var okText = !state.q || haystack.indexOf(state.q) > -1;
      var show = okLang && okText;
      card.hidden = !show;
      if (show) { shown += 1; }
    });
    if (shown === total) {
      status.textContent = total + (total === 1 ? " book" : " books");
    } else if (shown === 0) {
      status.textContent = "No books match. Try a different search or language filter.";
    } else {
      status.textContent = "Showing " + shown + " of " + total + " books";
    }
    if (emptyState) { emptyState.hidden = shown !== 0; }
    chips.forEach(function (chip) {
      var active = chip.getAttribute("data-language") === state.lang;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function clearAll() {
    state.lang = "all";
    state.q = "";
    if (search) { search.value = ""; }
    apply();
    if (search) { search.focus(); }
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      state.lang = chip.getAttribute("data-language");
      apply();
    });
  });

  if (search) {
    var timer = null;
    search.addEventListener("input", function () {
      if (timer) { window.clearTimeout(timer); }
      var value = search.value.trim().toLowerCase();
      timer = window.setTimeout(function () {
        state.q = value;
        apply();
      }, 120);
    });
    search.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && search.value) {
        search.value = "";
        state.q = "";
        apply();
      }
    });
  }

  if (clearButton) {
    clearButton.addEventListener("click", clearAll);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) { return; }
    var target = event.target;
    var tag = target && target.tagName;
    if (tag && /input|textarea|select/i.test(tag)) { return; }
    if (target && target.isContentEditable) { return; }
    if (!search) { return; }
    event.preventDefault();
    search.focus();
  });

  apply();
})();
