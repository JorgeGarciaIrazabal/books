/* Browser EPUB reader for the public library.
   Only books listed in catalog.json can be opened; no arbitrary EPUB
   URLs are loaded. Reads and saves the position in localStorage when
   the browser allows it, and supports both reflowable and fixed-layout
   EPUBs through EPUB.js. */
(function () {
  "use strict";

  function byId(id) { return document.getElementById(id); }

  var statusEl = byId("reader-status");
  var frame = byId("epub-frame");
  var tocPanel = byId("toc-panel");
  var tocList = byId("toc-list");
  var tocBackdrop = byId("toc-backdrop");
  var tocToggle = byId("toc-toggle");
  var tocClose = byId("toc-close");
  var prevBtn = byId("prev");
  var nextBtn = byId("next");
  var fontBox = byId("font-controls");
  var fontSmaller = byId("font-smaller");
  var fontLarger = byId("font-larger");
  var startOverBtn = byId("start-over");
  var titleEl = byId("book-title");
  var loadingEl = byId("reader-loading");
  var progressFill = byId("progress-fill");

  function say(message, isError) {
    if (statusEl) {
      statusEl.textContent = message;
      statusEl.classList.toggle("is-error", Boolean(isError));
    }
  }

  function hideLoading() {
    if (loadingEl) { loadingEl.hidden = true; }
  }

  function storageWorks() {
    try {
      var key = "__reader_probe__";
      window.localStorage.setItem(key, "1");
      window.localStorage.removeItem(key);
      return true;
    } catch (err) {
      return false;
    }
  }

  var canStore = storageWorks();

  var params = new URLSearchParams(window.location.search);
  var bookId = (params.get("book") || "").trim().toLowerCase();

  if (!/^[a-z0-9][a-z0-9-]*$/.test(bookId)) {
    say("No book was selected. Go back to the library and choose a title.", true);
    hideLoading();
    return;
  }
  if (typeof window.ePub !== "function" || typeof window.JSZip === "undefined") {
    say("The reader engine did not load. Refresh the page, or return to the library and try again.", true);
    hideLoading();
    return;
  }

  fetch("catalog.json").then(function (response) {
    if (!response.ok) { throw new Error("catalog request failed with " + response.status); }
    return response.json();
  }).then(function (catalog) {
    var book = null;
    (catalog.books || []).forEach(function (entry) {
      if (entry.id === bookId) { book = entry; }
    });
    if (!book) {
      say("This book is not in the library catalog. Go back to the library and choose a title.", true);
      return;
    }
    start(book);
  }).catch(function () {
    say("The library catalog could not be loaded. Refresh the page, or return to the library.", true);
  });

  function start(book) {
    titleEl.textContent = book.title;
    document.title = book.title + " · Books reader";
    document.body.classList.add(book.layout === "fixed" ? "is-fixed" : "is-reflowable");
    if (loadingEl) { loadingEl.hidden = false; }

    var epubUrl = book.downloads && book.downloads.epub;
    if (!epubUrl || epubUrl.indexOf("publications/") !== 0) {
      say("This book has no EPUB edition in the catalog.", true);
      hideLoading();
      return;
    }

    var epubBook;
    var rendition;
    try {
      epubBook = window.ePub(epubUrl);
      rendition = epubBook.renderTo(frame, {
        width: "100%",
        height: "100%",
        flow: "paginated",
        spread: book.layout === "fixed" ? "none" : "auto",
        minSpreadWidth: 1200
      });
    } catch (err) {
      say("The reader could not start for this book.", true);
      hideLoading();
      return;
    }

    epubBook.on("openFailed", function () {
      say("This book could not be opened. The file may be missing or damaged.", true);
      hideLoading();
    });

    if (!canStore) {
      say("This browser mode cannot save reading positions.");
    } else {
      say("Loading " + book.title + ". A large picture book can take a moment.");
    }

    /* ---------- text size (reflowable books only) ---------- */

    var scale = 100;
    if (canStore && book.layout !== "fixed") {
      try {
        var savedPrefs = JSON.parse(window.localStorage.getItem("reader-prefs:" + bookId) || "null");
        if (savedPrefs && savedPrefs.scale) { scale = savedPrefs.scale; }
      } catch (err) { /* ignore malformed saved preferences */ }
    }

    function savePrefs() {
      if (!canStore) { return; }
      try {
        window.localStorage.setItem("reader-prefs:" + bookId, JSON.stringify({ scale: scale }));
      } catch (err) { /* storage may be full */ }
    }

    function applyFont() {
      try { rendition.themes.fontSize(scale + "%"); }
      catch (err) { /* not all renditions support themes */ }
    }

    function updateFontButtons() {
      if (!fontSmaller || !fontLarger) { return; }
      fontSmaller.disabled = scale <= 90;
      fontLarger.disabled = scale >= 170;
    }

    if (book.layout !== "fixed") {
      fontBox.hidden = false;
      updateFontButtons();
      fontSmaller.addEventListener("click", function () {
        if (scale > 90) {
          scale -= 10;
          savePrefs();
          applyFont();
          updateFontButtons();
          say("Text size " + scale + "%.");
        }
      });
      fontLarger.addEventListener("click", function () {
        if (scale < 170) {
          scale += 10;
          savePrefs();
          applyFont();
          updateFontButtons();
          say("Text size " + scale + "%.");
        }
      });
    }

    /* ---------- fixed-layout page proportions ---------- */

    function applyFixedRatio() {
      if (book.layout !== "fixed" || frame.getAttribute("data-page-ratio")) { return; }
      var contents;
      try { contents = rendition.getContents(); }
      catch (err) { return; }
      if (!contents || !contents.length) { return; }
      var doc = contents[0] && contents[0].document;
      var body = doc && doc.body;
      if (!body) { return; }
      var w = body.offsetWidth;
      var h = body.offsetHeight;
      if (!w || !h) { return; }
      var ratio = w / h;
      frame.setAttribute("data-page-ratio", ratio.toFixed(4));
      frame.style.setProperty("--book-ratio", String(ratio));
      window.setTimeout(function () {
        try { rendition.resize(); } catch (err) { /* keep current size */ }
      }, 40);
    }

    /* ---------- table of contents ---------- */

    var chapterByHref = {};

    function buildToc(items, parent) {
      (items || []).forEach(function (item) {
        var li = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = String(item.label || "").trim();
        button.setAttribute("data-href", item.href || "");
        button.addEventListener("click", function () {
          rendition.display(item.href).catch(function () {
            say("That part of the book could not be opened.", true);
          });
          closeToc(true);
        });
        var clean = String(item.href || "").split("#")[0].replace(/^\//, "");
        if (clean && !chapterByHref[clean]) { chapterByHref[clean] = button.textContent; }
        li.appendChild(button);
        if (item.subitems && item.subitems.length) {
          var sub = document.createElement("ol");
          buildToc(item.subitems, sub);
          li.appendChild(sub);
        }
        parent.appendChild(li);
      });
    }

    function chapterLabelFor(href) {
      var clean = String(href || "").split("#")[0].replace(/^\//, "");
      if (chapterByHref[clean]) { return chapterByHref[clean]; }
      var keys = Object.keys(chapterByHref);
      for (var i = 0; i < keys.length; i += 1) {
        if (keys[i].indexOf(clean) === 0 || clean.indexOf(keys[i]) === 0) {
          return chapterByHref[keys[i]];
        }
      }
      return "";
    }

    function spineCount() {
      try {
        var spine = epubBook.spine;
        if (spine && spine.spineItems) { return spine.spineItems.length; }
        if (spine && spine.items) { return spine.items.length; }
        if (spine && typeof spine.each === "function") {
          var n = 0;
          spine.each(function () { n += 1; });
          return n;
        }
      } catch (err) { /* fall through */ }
      return 0;
    }

    function updateProgress(location) {
      if (!progressFill || !location || !location.start) { return; }
      var pct = 0;
      var total = spineCount();
      if (book.layout === "fixed") {
        if (total && location.start.index != null) {
          pct = (location.start.index + 1) / total;
        }
      } else if (typeof location.start.percentage === "number" && location.start.location >= 0) {
        pct = location.start.percentage;
      } else if (total && location.start.index != null) {
        /* EPUB.js only computes a percentage after locations are generated,
           which we skip to keep opening a book instant. The spine index and
           the current page within the section give an honest approximation. */
        var within = 0;
        var displayed = location.start.displayed;
        if (displayed && displayed.total) {
          within = Math.max(0, (displayed.page - 1) / displayed.total);
        }
        pct = (location.start.index + within) / total;
      }
      pct = Math.max(0, Math.min(1, pct));
      progressFill.style.width = Math.round(pct * 1000) / 10 + "%";
    }

    rendition.on("relocated", function (location) {
      if (!location || !location.start) { return; }
      hideLoading();
      applyFixedRatio();
      updateProgress(location);
      if (canStore && location.start.cfi) {
        try {
          window.localStorage.setItem(
            "reader-position:" + bookId,
            JSON.stringify({ cfi: location.start.cfi })
          );
        } catch (err) { /* storage unavailable or full */ }
      }
      var label = chapterLabelFor(location.start.href);
      var text;
      if (book.layout === "fixed" && location.start.index != null) {
        var total = spineCount();
        text = "Page " + (location.start.index + 1) + (total ? " of " + total : "");
        if (label) { text += " · " + label; }
      } else {
        text = label ? ("Reading: " + label) : "Page turned.";
        if (location.start.displayed && location.start.displayed.page) {
          text += " · page " + location.start.displayed.page +
                  " of " + location.start.displayed.total;
        }
      }
      say(text);
      markCurrentToc(location.start.href);
    });

    rendition.on("rendered", applyFixedRatio);

    function markCurrentToc(href) {
      var clean = String(href || "").split("#")[0].replace(/^\//, "");
      var buttons = tocList.querySelectorAll("button[data-href]");
      for (var i = 0; i < buttons.length; i += 1) {
        var buttonHref = buttons[i].getAttribute("data-href").split("#")[0].replace(/^\//, "");
        var matches = Boolean(buttonHref) && Boolean(clean) &&
          (buttonHref === clean || clean.indexOf(buttonHref) === 0 || buttonHref.indexOf(clean) === 0);
        buttons[i].classList.toggle("is-current", matches);
        if (matches) { buttons[i].setAttribute("aria-current", "true"); }
        else { buttons[i].removeAttribute("aria-current"); }
      }
    }

    function openToc() {
      tocBackdrop.hidden = false;
      window.requestAnimationFrame(function () {
        tocPanel.classList.add("is-open");
      });
      tocToggle.setAttribute("aria-expanded", "true");
    }

    function closeToc(restoreFocus) {
      tocPanel.classList.remove("is-open");
      tocBackdrop.hidden = true;
      tocToggle.setAttribute("aria-expanded", "false");
      if (restoreFocus && tocToggle.offsetParent !== null) {
        tocToggle.focus();
      }
    }

    tocBackdrop.hidden = true;
    tocToggle.addEventListener("click", function () {
      if (tocPanel.classList.contains("is-open")) { closeToc(true); }
      else { openToc(); }
    });
    tocBackdrop.addEventListener("click", function () { closeToc(true); });
    if (tocClose) {
      tocClose.addEventListener("click", function () { closeToc(true); });
    }

    /* ---------- paging ---------- */

    prevBtn.addEventListener("click", function () {
      rendition.prev().catch(function () { /* already at the beginning */ });
    });
    nextBtn.addEventListener("click", function () {
      rendition.next().catch(function () { /* already at the end */ });
    });

    document.addEventListener("keydown", function (event) {
      var tag = event.target && event.target.tagName;
      if (tag && /input|textarea|select/i.test(tag)) { return; }
      if (event.ctrlKey || event.metaKey || event.altKey) { return; }
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        rendition.next().catch(function () {});
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        rendition.prev().catch(function () {});
      } else if (event.key === "Escape") {
        if (tocPanel.classList.contains("is-open")) { closeToc(true); }
      }
    });

    startOverBtn.addEventListener("click", function () {
      if (canStore) {
        try { window.localStorage.removeItem("reader-position:" + bookId); }
        catch (err) { /* ignore */ }
      }
      rendition.display(0).catch(function () {
        rendition.display().catch(function () { /* keep current view */ });
      });
      if (progressFill) { progressFill.style.width = "0%"; }
      closeToc(true);
      say("Back at the beginning.");
    });

    /* ---------- initial display, restoring a saved position ---------- */

    var savedCfi = null;
    if (canStore) {
      try {
        var saved = JSON.parse(window.localStorage.getItem("reader-position:" + bookId) || "null");
        if (saved && saved.cfi) { savedCfi = saved.cfi; }
      } catch (err) { /* ignore malformed saved positions */ }
    }

    Promise.all([epubBook.ready, epubBook.loaded.navigation]).then(function (results) {
      var nav = results[1];
      var tocItems = Array.isArray(nav) ? nav : (nav && nav.toc) || [];
      buildToc(tocItems, tocList);
      applyFont();
      var target = savedCfi || undefined;
      return rendition.display(target).catch(function () {
        if (target) {
          return rendition.display();
        }
        throw new Error("Could not display the book content.");
      });
    }).catch(function (err) {
      hideLoading();
      say("The book could not be opened. " + (err && err.message ? err.message : ""), true);
    });
  }
})();
