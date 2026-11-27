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
  var viewToggle = byId("view-toggle");
  var textView = byId("text-view");
  var startOverBtn = byId("start-over");
  var titleEl = byId("book-title");
  var loadingEl = byId("reader-loading");
  var progressFill = byId("progress-fill");
  var narrationBar = byId("narration-bar");
  var listenToggle = byId("listen-toggle");
  var listenLabel = byId("listen-label");
  var listenIcon = byId("listen-icon");
  var narrationNote = byId("narration-note");

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

    var fixed = book.layout === "fixed";
    var savedView = null;
    if (fixed && canStore) {
      try {
        savedView = window.localStorage.getItem("reader-view:" + bookId);
        if (savedView !== "text" && savedView !== "page") { savedView = null; }
      } catch (err) { savedView = null; }
    }
    var defaultText = fixed && (
      window.matchMedia("(max-width: 599px)").matches ||
      window.matchMedia("(max-height: 520px)").matches ||
      window.matchMedia("(orientation: landscape) and (max-width: 1399px) and (max-height: 820px)").matches
    );
    var currentMode = fixed ? (savedView || (defaultText ? "text" : "page")) : "page";
    var currentHref = "";
    var currentCfi = "";
    var currentIndex = 0;
    var textSections = [];
    var textSectionsPromise = null;
    var textModeReady = false;
    var textViewRendered = false;
    var imageObserver = null;
    var textScrollFrame = null;
    var fontScrollFrame = null;
    var lastTextScrollTop = 0;
    var savedScrollApplied = false;
    var currentTextIndex = 0;
    var currentTextHref = "";

    var savedPosition = null;
    if (canStore) {
      try {
        savedPosition = JSON.parse(window.localStorage.getItem("reader-position:" + bookId) || "null");
      } catch (err) { savedPosition = null; }
    }
    var savedCfi = savedPosition && savedPosition.cfi ? savedPosition.cfi : null;
    var savedHref = savedPosition && savedPosition.href ? savedPosition.href : null;
    var savedSection = savedPosition && typeof savedPosition.section === "number"
      ? savedPosition.section
      : null;
    var savedScroll = savedPosition && typeof savedPosition.scroll === "number"
      ? savedPosition.scroll
      : null;

    function updateViewToggle() {
      if (!viewToggle || !fixed) { return; }
      var isText = currentMode === "text";
      viewToggle.textContent = isText ? "Pages" : "Text";
      viewToggle.setAttribute("aria-pressed", isText ? "true" : "false");
      viewToggle.setAttribute("aria-label", isText
        ? "Switch to the illustrated page view"
        : "Switch to the text reading view");
    }

    function updatePagerLabels() {
      var isText = currentMode === "text";
      if (prevBtn) { prevBtn.setAttribute("aria-label", isText ? "Scroll back" : "Previous page"); }
      if (nextBtn) { nextBtn.setAttribute("aria-label", isText ? "Scroll forward" : "Next page"); }
    }

    if (viewToggle) {
      viewToggle.hidden = !fixed;
      viewToggle.disabled = fixed;
      updateViewToggle();
    }

    var epubUrl = book.downloads && book.downloads.epub;
    if (!epubUrl || epubUrl.indexOf("publications/") !== 0) {
      say("This book has no EPUB edition in the catalog.", true);
      hideLoading();
      return;
    }

    /* ---------- narration (page audio for fixed-layout books) ---------- */

    var narration = book.layout === "fixed" && book.narration ? book.narration : null;
    var narrationFiles = {};
    var narrationPages = 0;
    var narrationAudio = null;
    var narrationPreload = null;
    var narrationOn = false;
    var narrationPageNumber = 0;
    var narrationSwitching = false;

    function narrationAvailable() {
      return Boolean(narration) && narrationPages > 0;
    }

    function updateNarrationUI() {
      if (listenToggle) {
        listenToggle.setAttribute("aria-pressed", narrationOn ? "true" : "false");
        listenToggle.setAttribute("aria-label", narrationOn
          ? "Pause the narration" : "Read this book aloud from the current page");
        if (listenLabel) { listenLabel.textContent = narrationOn ? "Pause" : "Listen"; }
        if (listenIcon) { listenIcon.textContent = narrationOn ? "❚❚" : "▶"; }
      }
      markNarratingPage();
    }

    function markNarratingPage() {
      if (!textView || !textViewRendered || !textView.querySelectorAll) { return; }
      var articles = textView.querySelectorAll(".text-page");
      for (var i = 0; i < articles.length; i += 1) {
        articles[i].classList.toggle("is-narrating",
          narrationOn && i === narrationPageNumber - 1);
      }
    }

    function currentPageNumber() {
      if (fixed && currentMode === "text") { return currentTextIndex + 1; }
      return (currentIndex || 0) + 1;
    }

    function narrationFileFor(page) {
      return narrationFiles[page] || null;
    }

    function ensureNarrationAudio() {
      if (narrationAudio) { return narrationAudio; }
      narrationAudio = new Audio();
      narrationAudio.preload = "auto";
      narrationAudio.addEventListener("ended", onNarrationEnded);
      narrationAudio.addEventListener("error", function () {
        stopNarration(true);
        say("That page's narration could not be played. You can keep reading.", true);
      });
      return narrationAudio;
    }

    function narrationSrc(file) {
      var base = new URL(narration.manifest, window.location.href);
      return new URL(file.src, base).href;
    }

    function playNarrationPage(page) {
      var file = narrationFileFor(page);
      if (!file) {
        stopNarration(true);
        say("Narration is not available for this page. You can keep reading.", true);
        return;
      }
      var audio = ensureNarrationAudio();
      var src = narrationSrc(file);
      narrationPageNumber = page;
      markNarratingPage();
      if (audio.src !== src) { audio.src = src; }
      if (audio.paused) {
        var started = audio.play();
        if (started && started.catch) {
          started.catch(function (error) {
            /* A page turn aborts the previous play() call; that is expected. */
            if (error && error.name === "AbortError") { return; }
            if (!narrationOn || audioPageChanged()) { return; }
            stopNarration(true);
            say("Narration could not start. You can keep reading.", true);
          });
        }
      }
      preloadNarrationPage(page + 1);
    }

    function audioPageChanged() {
      return currentPageNumber() !== narrationPageNumber;
    }

    function preloadNarrationPage(page) {
      var file = narrationFileFor(page);
      if (!file) { return; }
      if (!narrationPreload) {
        narrationPreload = new Audio();
        narrationPreload.preload = "auto";
      }
      var src = narrationSrc(file);
      if (narrationPreload.src !== src) { narrationPreload.src = src; }
    }

    function advanceForNarration(page) {
      narrationSwitching = true;
      var step;
      if (fixed && currentMode === "text") {
        scrollToTextIndex(page - 1, "auto");
        step = Promise.resolve();
      } else {
        step = displayPage(page - 1);
      }
      return Promise.resolve(step).then(function () {
        narrationSwitching = false;
        if (narrationOn) { playNarrationPage(page); }
      });
    }

    function onNarrationEnded() {
      if (!narrationOn) { return; }
      var next = narrationPageNumber + 1;
      if (next > narrationPages) {
        stopNarration(true);
        say("Narration finished.");
        return;
      }
      advanceForNarration(next);
    }

    function stopNarration(silent) {
      narrationOn = false;
      if (narrationAudio) {
        narrationAudio.pause();
        narrationAudio.currentTime = 0;
      }
      narrationPageNumber = 0;
      if (narrationPreload) { narrationPreload.removeAttribute("src"); }
      updateNarrationUI();
      if (!silent) { say("Narration paused."); }
    }

    function toggleNarration() {
      if (!narrationAvailable()) { return; }
      if (narrationOn) { stopNarration(); return; }
      narrationOn = true;
      updateNarrationUI();
      playNarrationPage(currentPageNumber());
    }

    function narrationPageChanged() {
      if (!narrationOn || narrationSwitching) { return; }
      var page = currentPageNumber();
      if (page === narrationPageNumber) { return; }
      if (!narrationFileFor(page)) { stopNarration(true); return; }
      playNarrationPage(page);
    }

    if (narration) {
      fetch(narration.manifest).then(function (response) {
        if (!response.ok) { throw new Error("narration manifest"); }
        return response.json();
      }).then(function (data) {
        (data.files || []).forEach(function (file) {
          if (file && file.page && file.src) { narrationFiles[file.page] = file; }
        });
        narrationPages = data.pages || 0;
        narration.credit = narration.credit || data.credit || "";
        if (!narrationAvailable()) { return; }
        if (narrationBar) { narrationBar.hidden = false; }
        var minutes = Math.max(1, Math.round((data.seconds || 0) / 60));
        var summary = narrationPages + " pages · about " + minutes + " min";
        if (narrationNote) {
          narrationNote.textContent = summary;
          if (narration.credit) { narrationNote.title = narration.credit; }
        }
        if (narrationBar) {
          narrationBar.setAttribute("aria-label",
            "Read aloud" + (narration.credit ? ". " + narration.credit : "") + ". " + summary + ".");
        }
        updateNarrationUI();
        if (listenToggle) { listenToggle.addEventListener("click", toggleNarration); }
      }).catch(function () {
        if (narrationBar) { narrationBar.hidden = true; }
        narration = null;
      });
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

    /* ---------- text size ---------- */

    function defaultReadingScale() {
      if (window.matchMedia("(max-width: 599px)").matches) { return 115; }
      if (window.matchMedia("(max-width: 1099px)").matches) { return 110; }
      return 100;
    }

    var scale = fixed ? 100 : defaultReadingScale();
    if (canStore) {
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

    function cancelFontScrollRestore() {
      if (fontScrollFrame) {
        window.cancelAnimationFrame(fontScrollFrame);
        fontScrollFrame = null;
      }
    }

    function applyFont(preserveScroll) {
      if (fixed) {
        if (!textView) { return; }
        var max = textView.scrollHeight - textView.clientHeight;
        var ratio = max > 0 ? textView.scrollTop / max : 0;
        textView.style.setProperty("--text-scale", String(scale / 100));
        cancelFontScrollRestore();
        if (preserveScroll && textViewRendered && currentMode === "text") {
          fontScrollFrame = window.requestAnimationFrame(function () {
            fontScrollFrame = null;
            var newMax = textView.scrollHeight - textView.clientHeight;
            textView.scrollTop = ratio * newMax;
            updateTextProgress();
            updateTextStatus(currentTextIndex);
          });
        }
        return;
      }
      try { rendition.themes.fontSize(scale + "%"); }
      catch (err) { /* not all renditions support themes */ }
    }

    function updateFontButtons() {
      if (!fontSmaller || !fontLarger) { return; }
      fontSmaller.disabled = scale <= 90;
      fontLarger.disabled = scale >= 170;
    }

    if (fontBox && fontSmaller && fontLarger) {
      if (!fixed) { fontBox.hidden = false; }
      updateFontButtons();
      fontSmaller.addEventListener("click", function () {
        if (scale > 90) {
          scale -= 10;
          savePrefs();
          applyFont(true);
          updateFontButtons();
          say("Text size " + scale + "%.");
        }
      });
      fontLarger.addEventListener("click", function () {
        if (scale < 170) {
          scale += 10;
          savePrefs();
          applyFont(true);
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
          if (fixed && currentMode === "text") {
            var index = hrefToIndex(item.href);
            if (index >= 0) { scrollToTextIndex(index, "auto"); }
            else {
              rendition.display(item.href).catch(function () {
                say("That part of the book could not be opened.", true);
              });
            }
          } else {
            rendition.display(item.href).catch(function () {
              say("That part of the book could not be opened.", true);
            });
          }
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
      currentHref = location.start.href || "";
      currentCfi = location.start.cfi || "";
      currentIndex = location.start.index != null ? location.start.index : 0;

      /* The text view owns progress, status and position while it is active. */
      if (fixed && currentMode === "text" && textModeReady) {
        hideLoading();
        return;
      }

      applyFixedRatio();
      updateProgress(location);
      if (canStore && location.start.cfi) {
        try {
          window.localStorage.setItem(
            "reader-position:" + bookId,
            JSON.stringify({ cfi: location.start.cfi, href: currentHref })
          );
        } catch (err) { /* storage unavailable or full */ }
      }
      var label = chapterLabelFor(currentHref);
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
      markCurrentToc(currentHref);
      narrationPageChanged();

      if (fixed && currentMode === "text" && !textModeReady) {
        activateInitialTextMode();
      } else {
        hideLoading();
      }
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

    /* ---------- adaptive text view (fixed-layout books) ---------- */

    function normalizeHref(href) {
      return String(href || "").split("#")[0].replace(/^\//, "");
    }

    function hrefToIndex(href) {
      var clean = normalizeHref(href);
      if (!clean) { return -1; }
      for (var i = 0; i < textSections.length; i += 1) {
        if (normalizeHref(textSections[i].href) === clean) { return i; }
      }
      return -1;
    }

    function buildTextSections() {
      if (textSectionsPromise) { return textSectionsPromise; }
      var spine = [];
      try {
        spine = (epubBook.spine && (epubBook.spine.spineItems || epubBook.spine.items)) || [];
      } catch (err) { spine = []; }
      if (!spine.length) {
        textSectionsPromise = Promise.reject(new Error("This book has no pages."));
        return textSectionsPromise;
      }
      textSectionsPromise = Promise.all(spine.map(function (section, index) {
        return epubBook.load(section.href).then(function (doc) {
          return {
            index: index,
            href: section.href,
            url: section.url,
            title: (doc.querySelector("title") && doc.querySelector("title").textContent) || "",
            story: doc.querySelector(".story"),
            h1: doc.querySelector("h1"),
            chapterHeading: doc.querySelector(".chapter-heading"),
            images: Array.prototype.map.call(doc.querySelectorAll("figure img"), function (img) {
              var style = img.getAttribute("style") || "";
              var widthMatch = /width\s*:\s*([\d.]+)in/i.exec(style);
              var heightMatch = /height\s*:\s*([\d.]+)in/i.exec(style);
              var ratio = (widthMatch && heightMatch && parseFloat(heightMatch[1]))
                ? parseFloat(widthMatch[1]) / parseFloat(heightMatch[1])
                : 0;
              return {
                src: img.getAttribute("src") || "",
                alt: img.getAttribute("alt") || "",
                ratio: ratio
              };
            })
          };
        }).catch(function () {
          return { index: index, href: section.href, url: section.url, error: true, images: [] };
        });
      })).then(function (sections) {
        textSections = sections;
        return sections;
      });
      return textSectionsPromise;
    }

    /* Clone only safe reading content. Inline positions, sizes, ids, links and
       event handlers are dropped; classes are kept for chapter styling. */
    function cleanClone(node) {
      if (!node) { return null; }
      var clone;
      try { clone = document.importNode(node, true); }
      catch (err) { return null; }
      var bad = clone.querySelectorAll
        ? clone.querySelectorAll("script, style, iframe, object, embed, link, meta, img, video, audio, source")
        : [];
      for (var i = bad.length - 1; i >= 0; i -= 1) {
        if (bad[i].parentNode) { bad[i].parentNode.removeChild(bad[i]); }
      }
      if (clone.querySelectorAll) {
        var elements = clone.querySelectorAll("*");
        for (var j = 0; j < elements.length; j += 1) {
          var attrs = elements[j].attributes;
          for (var k = attrs.length - 1; k >= 0; k -= 1) {
            if (attrs[k].name !== "class") { elements[j].removeAttribute(attrs[k].name); }
          }
        }
      }
      var rootAttrs = clone.attributes;
      if (rootAttrs) {
        for (var m = rootAttrs.length - 1; m >= 0; m -= 1) {
          if (rootAttrs[m].name !== "class") { clone.removeAttribute(rootAttrs[m].name); }
        }
      }
      return clone;
    }

    function resolveImagePath(section, src) {
      if (!src || !section || !section.url || /^(?:data:|https?:|blob:)/i.test(src)) { return ""; }
      try {
        return new URL(src, "https://epub.local" + section.url).pathname;
      } catch (err) { return ""; }
    }

    function loadTextImage(img) {
      var path = img.getAttribute("data-epub-path");
      if (!path || img.getAttribute("src")) { return; }
      epubBook.archive.createUrl(path).then(function (url) {
        img.src = url;
      }).catch(function () {
        var figure = img.closest ? img.closest("figure") : null;
        if (figure && figure.parentNode) { figure.parentNode.removeChild(figure); }
      });
    }

    function ensureImageObserver() {
      if (imageObserver || typeof window.IntersectionObserver !== "function") {
        return imageObserver;
      }
      imageObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) { return; }
          imageObserver.unobserve(entry.target);
          loadTextImage(entry.target);
        });
      }, { root: textView, rootMargin: "600px 0px" });
      return imageObserver;
    }

    function updateTextProgress() {
      if (!progressFill || !textView) { return; }
      var max = textView.scrollHeight - textView.clientHeight;
      var pct = max > 0 ? textView.scrollTop / max : 0;
      pct = Math.max(0, Math.min(1, pct));
      progressFill.style.width = Math.round(pct * 1000) / 10 + "%";
    }

    function updateTextStatus(index) {
      var total = textSections.length;
      var text = "Page " + (index + 1) + (total ? " of " + total : "");
      var label = chapterLabelFor(textSections[index] && textSections[index].href);
      if (label) { text += " · " + label; }
      say(text);
    }

    function saveTextPosition() {
      if (!canStore || !textView) { return; }
      try {
        window.localStorage.setItem(
          "reader-position:" + bookId,
          JSON.stringify({
            href: currentTextHref,
            section: currentTextIndex,
            scroll: Math.round(textView.scrollTop)
          })
        );
      } catch (err) { /* storage may be full */ }
    }

    var saveTextTimer = null;
    function scheduleSaveTextPosition() {
      if (!canStore) { return; }
      window.clearTimeout(saveTextTimer);
      saveTextTimer = window.setTimeout(saveTextPosition, 350);
    }

    function setCurrentTextIndex(index, force) {
      if (!textSections.length) { return; }
      if (index < 0) { index = 0; }
      if (index >= textSections.length) { index = textSections.length - 1; }
      if (!force && index === currentTextIndex) { return; }
      currentTextIndex = index;
      if (textSections[index]) { currentTextHref = textSections[index].href; }
      updateTextStatus(index);
      updateTextProgress();
      markCurrentToc(currentTextHref);
      saveTextPosition();
      narrationPageChanged();
      if (narrationOn) { markNarratingPage(); }
    }

    function buildTextArticle(section, index) {
      var article = document.createElement("article");
      article.className = "text-page";
      article.id = "text-page-" + (index + 1);
      article.setAttribute("data-index", String(index));
      article.setAttribute("aria-label", "Page " + (index + 1) + " of " + textSections.length);

      if (section.error) {
        var error = document.createElement("p");
        error.className = "text-error";
        error.textContent = "This page could not be prepared in the text view.";
        article.appendChild(error);
      } else {
        var heading = cleanClone(section.h1);
        if (heading) {
          heading.classList.add("text-book-title");
          article.appendChild(heading);
        }
        var chapter = cleanClone(section.chapterHeading);
        if (chapter) {
          chapter.classList.add("text-chapter");
          article.appendChild(chapter);
        }
        if (section.story) {
          var story = cleanClone(section.story);
          if (story) {
            var wrapper = document.createElement("div");
            wrapper.className = "text-story";
            while (story.firstChild) { wrapper.appendChild(story.firstChild); }
            article.appendChild(wrapper);
          }
        }
        (section.images || []).forEach(function (image) {
          var path = resolveImagePath(section, image.src);
          if (!path) { return; }
          var figure = document.createElement("figure");
          figure.className = "text-illustration";
          var img = document.createElement("img");
          img.alt = image.alt;
          img.loading = "lazy";
          img.decoding = "async";
          img.setAttribute("data-epub-path", path);
          if (image.ratio) {
            img.setAttribute("width", "1000");
            img.setAttribute("height", String(Math.round(1000 / image.ratio)));
            figure.style.aspectRatio = String(image.ratio);
          }
          figure.appendChild(img);
          article.appendChild(figure);
          var observer = ensureImageObserver();
          if (observer) { observer.observe(img); }
          else { loadTextImage(img); }
        });
      }

      var folio = document.createElement("div");
      folio.className = "text-folio";
      folio.setAttribute("aria-hidden", "true");
      folio.textContent = String(index + 1);
      article.appendChild(folio);
      return article;
    }

    function renderTextSections() {
      if (!textView || textViewRendered) { return; }
      textView.innerHTML = "";
      var fragment = document.createDocumentFragment();
      textSections.forEach(function (section, index) {
        fragment.appendChild(buildTextArticle(section, index));
      });
      textView.appendChild(fragment);
      textViewRendered = true;
      currentTextIndex = 0;
      currentTextHref = textSections[0] ? textSections[0].href : "";
      applyFont();
      updateTextStatus(0);
      updateTextProgress();
      markCurrentToc(currentTextHref);
      markNarratingPage();
    }

    function scrollToTextIndex(index, behavior) {
      cancelFontScrollRestore();
      if (!textView || !textViewRendered) { return; }
      var articles = textView.querySelectorAll(".text-page");
      if (!articles.length) { return; }
      if (index < 0) { index = 0; }
      if (index >= articles.length) { index = articles.length - 1; }
      var top = index === 0 ? 0 : Math.max(0, articles[index].offsetTop - 8);
      textView.scrollTo({ top: top, behavior: behavior || "auto" });
      setCurrentTextIndex(index, true);
    }

    function onTextScroll() {
      cancelFontScrollRestore();
      if (!textViewRendered || currentMode !== "text" || textScrollFrame) { return; }
      textScrollFrame = window.requestAnimationFrame(function () {
        textScrollFrame = null;
        updateTextProgress();
        var articles = textView.querySelectorAll(".text-page");
        if (!articles.length) { return; }
        var probe = textView.scrollTop + Math.min(120, textView.clientHeight * 0.3);
        var index = 0;
        for (var i = 0; i < articles.length; i += 1) {
          if (articles[i].offsetTop <= probe) { index = i; }
          else { break; }
        }
        if (index !== currentTextIndex) { setCurrentTextIndex(index, false); }
        scheduleSaveTextPosition();
      });
    }

    function setMode(mode, options) {
      if (!fixed) { return false; }
      options = options || {};
      if (mode !== "text" && mode !== "page") { mode = "page"; }

      if (mode === "text") {
        if (!textSections.length) {
          say("The text view is not ready for this book.", true);
          return false;
        }
        var index = typeof options.index === "number" ? options.index : hrefToIndex(currentHref);
        if (index < 0) { index = currentTextIndex || 0; }
        if (index >= textSections.length) { index = textSections.length - 1; }
        var previousIndex = currentTextIndex;
        var restoreScroll = textViewRendered && index === previousIndex;
        currentMode = "text";
        textModeReady = true;
        updateViewToggle();
        updatePagerLabels();
        document.body.classList.add("text-mode");
        frame.setAttribute("aria-hidden", "true");
        textView.hidden = false;
        if (fontBox) { fontBox.hidden = false; }
        renderTextSections();
        scrollToTextIndex(index, "auto");
        if (restoreScroll && lastTextScrollTop > 0) {
          textView.scrollTop = lastTextScrollTop;
          updateTextProgress();
        } else if (!savedScrollApplied && index === savedSection && savedScroll != null) {
          textView.scrollTop = Math.max(0, savedScroll);
          savedScrollApplied = true;
          updateTextProgress();
        }
        hideLoading();
        return true;
      }

      if (textView && textViewRendered) { lastTextScrollTop = textView.scrollTop; }
      currentMode = "page";
      textModeReady = false;
      updateViewToggle();
      updatePagerLabels();
      document.body.classList.remove("text-mode");
      textView.hidden = true;
      frame.removeAttribute("aria-hidden");
      if (fontBox) { fontBox.hidden = true; }
      var target = options.href || currentTextHref || currentHref;
      /* The font row disappears in page mode, so the frame grows. Resize the
         rendition to the new stage before displaying the remembered page;
         resizing after display can snap fixed-layout books back to page 1. */
      try { rendition.resize(); } catch (err) { /* keep the current size */ }
      if (target) {
        rendition.display(target).catch(function () { /* keep the current page */ });
      }
      hideLoading();
      return true;
    }

    function textNext() {
      cancelFontScrollRestore();
      if (!textSections.length || !textView) { return; }
      var behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
      textView.scrollBy({ top: Math.max(48, textView.clientHeight * 0.85), behavior: behavior });
    }

    function textPrev() {
      cancelFontScrollRestore();
      if (!textSections.length || !textView) { return; }
      var behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
      textView.scrollBy({ top: -Math.max(48, textView.clientHeight * 0.85), behavior: behavior });
    }

    function activateInitialTextMode() {
      var restore = (savedSection != null && savedSection >= 0) ? savedSection : undefined;
      var apply = function () {
        if (!textSections.length) {
          currentMode = "page";
          textModeReady = false;
          updateViewToggle();
          hideLoading();
          say("The text view could not be prepared. Showing the illustrated pages.", true);
          return;
        }
        setMode("text", { index: restore });
      };
      if (textSectionsPromise) {
        textSectionsPromise.then(apply).catch(function () {
          currentMode = "page";
          textModeReady = false;
          updateViewToggle();
          hideLoading();
          say("The text view could not be prepared. Showing the illustrated pages.", true);
        });
      } else {
        apply();
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

    if (viewToggle && fixed) {
      viewToggle.addEventListener("click", function () {
        if (currentMode === "text") {
          if (setMode("page") && canStore) {
            try { window.localStorage.setItem("reader-view:" + bookId, "page"); }
            catch (err) { /* storage may be full */ }
          }
          return;
        }
        var switchToText = function () {
          if (setMode("text") && canStore) {
            try { window.localStorage.setItem("reader-view:" + bookId, "text"); }
            catch (err) { /* storage may be full */ }
          }
        };
        if (!textSections.length) {
          if (!textSectionsPromise) { buildTextSections(); }
          if (textSectionsPromise) {
            say("Preparing the text view…");
            textSectionsPromise.then(switchToText).catch(function () {
              say("The text view could not be prepared.", true);
            });
          } else {
            say("The text view could not be prepared.", true);
          }
          return;
        }
        switchToText();
      });
    }

    /* ---------- paging ---------- */

    /* EPUB.js can drop the first next()/prev() call before the initial
       location settles, so verify that the location actually moved and retry
       once. Auto-advance uses rendition.display(page) and is unaffected. */
    function spineHrefAt(index) {
      try {
        var spine = (epubBook.spine && (epubBook.spine.spineItems || epubBook.spine.items)) || [];
        var item = spine[index];
        return item && item.href ? item.href : "";
      } catch (err) { return ""; }
    }

    function displayPage(index) {
      var href = spineHrefAt(index);
      return rendition.display(href || index).catch(function () { /* keep the page */ });
    }

    function turnPage(direction, attempt) {
      attempt = attempt || 0;
      if (fixed) {
        var total = spineCount();
        var target = currentIndex + direction;
        if (total && (target < 0 || target >= total)) { return; }
        displayPage(target);
        return;
      }
      var before = currentHref;
      var step = direction > 0 ? rendition.next() : rendition.prev();
      function retryIfStuck() {
        if (attempt < 1 && currentHref === before) {
          turnPage(direction, attempt + 1);
        }
      }
      if (step && step.then) { step.then(function () { window.setTimeout(retryIfStuck, 260); }).catch(function () {}); }
      else { window.setTimeout(retryIfStuck, 260); }
    }

    if (textView) {
      textView.addEventListener("scroll", onTextScroll, { passive: true });
    }

    prevBtn.addEventListener("click", function () {
      if (fixed && currentMode === "text") { textPrev(); return; }
      turnPage(-1);
    });
    nextBtn.addEventListener("click", function () {
      if (fixed && currentMode === "text") { textNext(); return; }
      turnPage(1);
    });

    document.addEventListener("keydown", function (event) {
      var tag = event.target && event.target.tagName;
      if (tag && /input|textarea|select/i.test(tag)) { return; }
      if (event.ctrlKey || event.metaKey || event.altKey) { return; }
      if (fixed && currentMode === "text") {
        if (event.key === "ArrowRight" || event.key === "PageDown") {
          event.preventDefault();
          textNext();
        } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
          event.preventDefault();
          textPrev();
        } else if (event.key === "Escape") {
          if (tocPanel.classList.contains("is-open")) { closeToc(true); }
        }
        return;
      }
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        turnPage(1);
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        turnPage(-1);
      } else if (event.key === "Escape") {
        if (tocPanel.classList.contains("is-open")) { closeToc(true); }
      }
    });

    startOverBtn.addEventListener("click", function () {
      if (narrationOn) { stopNarration(true); }
      if (canStore) {
        try { window.localStorage.removeItem("reader-position:" + bookId); }
        catch (err) { /* ignore */ }
      }
      if (fixed && currentMode === "text" && textSections.length) {
        lastTextScrollTop = 0;
        scrollToTextIndex(0, "auto");
      } else {
        rendition.display(0).catch(function () {
          rendition.display().catch(function () { /* keep current view */ });
        });
        if (progressFill) { progressFill.style.width = "0%"; }
      }
      closeToc(true);
      say("Back at the beginning.");
    });

    /* ---------- initial display, restoring a saved position ---------- */

    Promise.all([epubBook.ready, epubBook.loaded.navigation]).then(function (results) {
      var nav = results[1];
      var tocItems = Array.isArray(nav) ? nav : (nav && nav.toc) || [];
      buildToc(tocItems, tocList);
      applyFont();
      if (viewToggle) { viewToggle.disabled = false; }
      if (fixed) {
        /* Parse the page documents alongside the first page render. This uses
           the archive EPUB.js already has in memory, so it costs no download. */
        buildTextSections().catch(function () { /* handled if text is requested */ });
      }
      var target = savedCfi || savedHref || undefined;
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
