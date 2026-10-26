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
  var prevBtn = byId("prev");
  var nextBtn = byId("next");
  var fontBox = byId("font-controls");
  var fontSmaller = byId("font-smaller");
  var fontLarger = byId("font-larger");
  var startOverBtn = byId("start-over");
  var titleEl = byId("book-title");

  function say(message, isError) {
    if (statusEl) {
      statusEl.textContent = message;
      statusEl.classList.toggle("is-error", Boolean(isError));
    }
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
    return;
  }
  if (typeof window.ePub !== "function" || typeof window.JSZip === "undefined") {
    say("The reader engine did not load. Refresh the page, or return to the library and try again.", true);
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

    var epubUrl = book.downloads && book.downloads.epub;
    if (!epubUrl || epubUrl.indexOf("publications/") !== 0) {
      say("This book has no EPUB edition in the catalog.", true);
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
        minSpreadWidth: 900
      });
    } catch (err) {
      say("The reader could not start for this book.", true);
      return;
    }

    epubBook.on("openFailed", function () {
      say("This book could not be opened. The file may be missing or damaged.", true);
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

    if (book.layout !== "fixed") {
      fontBox.hidden = false;
      fontSmaller.addEventListener("click", function () {
        if (scale > 90) {
          scale -= 10;
          savePrefs();
          applyFont();
          say("Text size " + scale + "%.");
        }
      });
      fontLarger.addEventListener("click", function () {
        if (scale < 170) {
          scale += 10;
          savePrefs();
          applyFont();
          say("Text size " + scale + "%.");
        }
      });
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
          closeToc();
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

    rendition.on("relocated", function (location) {
      if (!location || !location.start) { return; }
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
      tocPanel.hidden = false;
      tocBackdrop.hidden = false;
      window.requestAnimationFrame(function () {
        tocPanel.classList.add("is-open");
      });
      tocToggle.setAttribute("aria-expanded", "true");
    }

    function closeToc() {
      tocPanel.classList.remove("is-open");
      tocBackdrop.hidden = true;
      tocToggle.setAttribute("aria-expanded", "false");
    }

    tocPanel.hidden = false;
    tocBackdrop.hidden = true;
    tocToggle.addEventListener("click", function () {
      if (tocPanel.classList.contains("is-open")) { closeToc(); }
      else { openToc(); }
    });
    tocBackdrop.addEventListener("click", closeToc);

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
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        rendition.next().catch(function () {});
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        rendition.prev().catch(function () {});
      } else if (event.key === "Escape") {
        closeToc();
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
      say("The book could not be opened. " + (err && err.message ? err.message : ""), true);
    });
  }
})();