(function () {
  "use strict";
  var rows = Array.from(document.querySelectorAll(".chapter-audio li"));
  var panel = document.getElementById("audio-player");
  if (!panel || !rows.length) { return; }

  var control = document.getElementById("audio-control");
  var titleEl = document.getElementById("audio-current");
  var positionEl = document.getElementById("audio-position");
  var statusEl = document.getElementById("audio-status");
  var previousBtn = document.getElementById("audio-previous");
  var nextBtn = document.getElementById("audio-next");
  var downloadLink = document.getElementById("audio-download");
  var navContainer = panel.querySelector(".audio-player-nav");
  var linksContainer = panel.querySelector(".audio-links");
  var hintEl = panel.querySelector(".player-hint");
  var coverEl = panel.querySelector(".audio-cover");
  var eyebrowEl = panel.querySelector(".audio-eyebrow");
  var bookTitleEl = document.getElementById("book-title");

  var bookTitle = bookTitleEl ? bookTitleEl.textContent.trim() : document.title;
  var eyebrowText = eyebrowEl ? eyebrowEl.textContent.trim() : "";
  var coverSrc = coverEl ? coverEl.src : "";
  var coverAlt = coverEl ? coverEl.alt : ("Cover of " + bookTitle);

  var chapters = rows.map(function (row, index) {
    var heading = row.querySelector("h3");
    var rowAudio = row.querySelector("audio");
    var src = rowAudio ? rowAudio.getAttribute("src") : "";
    if (rowAudio) { rowAudio.remove(); }
    var button = document.createElement("button");
    button.type = "button";
    button.className = "chapter-select";
    var chapterTitle = heading ? heading.textContent.trim() : ("Chapter " + (index + 1));
    button.textContent = chapterTitle.replace(/^Chapter [^:]+:\s*/, "");
    button.setAttribute("aria-label", chapterTitle);
    var details = row.querySelector("p");
    var link = details ? details.querySelector("a") : null;
    var downloadHref = link ? link.href : src;
    if (link) { link.hidden = true; }
    if (heading) { heading.replaceWith(button); }
    button.addEventListener("click", function () {
      var wasPlaying = !player.paused && !player.ended;
      selectChapter(index, wasPlaying || index === current);
    });
    return {
      number: index + 1,
      button: button,
      title: chapterTitle,
      src: src,
      download: downloadHref,
      startSeconds: 0,
      seconds: 0,
      scenes: []
    };
  });

  if (!chapters.length || !chapters[0].src) { return; }

  var firstAudioUrl = new URL(chapters[0].src, window.location.href);
  var chaptersJsonUrl = new URL("chapters.json", firstAudioUrl).href;
  var pathParts = firstAudioUrl.pathname.split("/").filter(Boolean);
  var bookId = pathParts.length >= 2 ? pathParts[pathParts.length - 2] : "audiobook";
  var storageKey = "audiobook-pos:" + bookId;

  /* Always keep one persistent <audio> element so OS background/lock-screen
     playback never loses its audio session across chapter transitions. */
  var player = document.createElement("audio");
  player.controls = true;
  player.preload = "metadata";
  control.replaceChildren(player);

  var current = 0;
  var continuousMode = false;
  var fullBookUrl = "";
  var totalDuration = 0;
  var pendingSeek = null;
  var hasScenes = false;
  var activeSceneKey = "";
  var preloaderAudio = null;
  var lastSavedAt = 0;
  var lastPositionStateAt = 0;

  /* Add skip -15s / +15s buttons to player nav when present. */
  var skipBackBtn = null;
  var skipFwdBtn = null;
  if (navContainer && previousBtn && nextBtn) {
    skipBackBtn = document.createElement("button");
    skipBackBtn.type = "button";
    skipBackBtn.className = "audio-skip-btn";
    skipBackBtn.textContent = "−15s";
    skipBackBtn.setAttribute("aria-label", "Back 15 seconds");
    skipFwdBtn = document.createElement("button");
    skipFwdBtn.type = "button";
    skipFwdBtn.className = "audio-skip-btn";
    skipFwdBtn.textContent = "+15s";
    skipFwdBtn.setAttribute("aria-label", "Forward 15 seconds");
    navContainer.insertBefore(skipBackBtn, nextBtn);
    navContainer.insertBefore(skipFwdBtn, nextBtn);
    skipBackBtn.addEventListener("click", function () { seekBy(-15); });
    skipFwdBtn.addEventListener("click", function () { seekBy(15); });
  }

  function storageGet() {
    try {
      return JSON.parse(window.localStorage.getItem(storageKey) || "null");
    } catch (err) { return null; }
  }

  function storageSave(force) {
    var now = Date.now();
    if (!force && now - lastSavedAt < 3000) { return; }
    lastSavedAt = now;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({
        mode: continuousMode ? "full" : "track",
        chapter: current,
        time: Math.max(0, Math.round(player.currentTime * 10) / 10)
      }));
    } catch (err) { /* ignore storage errors */ }
  }

  function safePlay() {
    var p = player.play();
    if (p && typeof p.catch === "function") {
      p.catch(function (err) {
        if (err && err.name === "AbortError") { return; }
        statusEl.textContent = "Press play to continue listening.";
        updatePlayLabels();
      });
    }
  }

  function seekToTime(targetSec) {
    var sec = Math.max(0, Number(targetSec) || 0);
    if (player.readyState >= 1) {
      var maxDur = isFinite(player.duration) && player.duration > 0 ? player.duration : sec;
      pendingSeek = null;
      try { player.currentTime = Math.min(maxDur, sec); } catch (err) { /* keep time */ }
    } else {
      pendingSeek = sec;
    }
  }

  function seekBy(delta) {
    var base = pendingSeek !== null ? pendingSeek : (player.currentTime || 0);
    var target = Math.max(0, base + delta);
    if (continuousMode) {
      seekToTime(target);
      syncFromCurrentTime();
    } else {
      seekToTime(target);
      updateSceneForCurrentChapter();
    }
    updateMediaPositionState();
    storageSave(true);
  }

  function preloadTrack(index) {
    if (continuousMode || index < 0 || index >= chapters.length) { return; }
    if (!preloaderAudio) {
      preloaderAudio = new Audio();
      preloaderAudio.preload = "auto";
    }
    var abs = new URL(chapters[index].src, window.location.href).href;
    if (preloaderAudio.src !== abs) { preloaderAudio.src = abs; }
  }

  function setActiveChapterUI(index) {
    current = index;
    var ch = chapters[index];
    titleEl.textContent = ch.title;
    if (downloadLink) { downloadLink.href = ch.download; }
    positionEl.textContent = "Chapter " + (index + 1) + " of " + chapters.length;
    chapters.forEach(function (item, i) {
      if (i === index) { item.button.setAttribute("aria-current", "true"); }
      else { item.button.removeAttribute("aria-current"); }
    });
    if (previousBtn) { previousBtn.disabled = index === 0; }
    if (nextBtn) { nextBtn.disabled = index === chapters.length - 1; }
    if (lightboxRefs) {
      lightboxRefs.chapterEl.textContent = positionEl.textContent + " · " + ch.title;
      lightboxRefs.prevBtn.disabled = index === 0;
      lightboxRefs.nextBtn.disabled = index === chapters.length - 1;
    }
    preloadChapterScenes(ch);
  }

  function selectChapter(index, play) {
    if (index < 0) { index = 0; }
    if (index >= chapters.length) { index = chapters.length - 1; }
    var ch = chapters[index];
    statusEl.textContent = "";

    if (continuousMode) {
      setActiveChapterUI(index);
      seekToTime(ch.startSeconds || 0);
      updateSceneForTime(index, 0);
      updateMediaMetadata();
      updateMediaPositionState();
      storageSave(true);
      if (play) { safePlay(); }
      return;
    }

    var targetAbs = new URL(ch.src, window.location.href).href;
    var switchingSrc = player.src !== targetAbs;
    if (switchingSrc) {
      pendingSeek = null;
      player.src = ch.src;
      player.load();
    } else if (index !== current) {
      seekToTime(0);
    }
    setActiveChapterUI(index);
    updateSceneForTime(index, 0);
    updateMediaMetadata();
    updateMediaPositionState();
    storageSave(true);
    if (play) {
      preloadTrack(index + 1);
      safePlay();
    }
  }

  function chapterIndexForBookTime(bookSec) {
    var t = Math.max(0, bookSec);
    for (var i = chapters.length - 1; i >= 0; i -= 1) {
      if (t + 0.08 >= (chapters[i].startSeconds || 0)) { return i; }
    }
    return 0;
  }

  /* ---------- Lock-screen Media Session ---------- */

  function currentArtworkUrl() {
    if (hasScenes && storyRefs && storyRefs.currentImage) {
      return storyRefs.currentImage;
    }
    return coverSrc;
  }

  function updateMediaMetadata() {
    if (!("mediaSession" in navigator) || typeof window.MediaMetadata !== "function") { return; }
    var ch = chapters[current];
    if (!ch) { return; }
    var art = currentArtworkUrl();
    try {
      navigator.mediaSession.metadata = new window.MediaMetadata({
        title: ch.title,
        artist: bookTitle,
        album: eyebrowText || bookTitle,
        artwork: art ? [{ src: art, sizes: "720x1080", type: "image/jpeg" }] : []
      });
    } catch (err) { /* ignore unsupported metadata fields */ }
  }

  function updateMediaPositionState() {
    if (!("mediaSession" in navigator) || typeof navigator.mediaSession.setPositionState !== "function") { return; }
    var dur = isFinite(player.duration) && player.duration > 0 ? player.duration : totalDuration;
    if (!dur || dur <= 0) { return; }
    var pos = Math.max(0, Math.min(dur, player.currentTime || 0));
    try {
      navigator.mediaSession.setPositionState({
        duration: dur,
        playbackRate: player.playbackRate || 1,
        position: pos
      });
    } catch (err) { /* ignore transient duration states */ }
  }

  function initMediaSessionHandlers() {
    if (!("mediaSession" in navigator)) { return; }
    var handlers = {
      play: function () { safePlay(); },
      pause: function () { player.pause(); },
      previoustrack: function () {
        if (current > 0) { selectChapter(current - 1, !player.paused); }
        else { seekToTime(0); }
      },
      nexttrack: function () {
        if (current + 1 < chapters.length) { selectChapter(current + 1, !player.paused); }
      },
      seekbackward: function (details) { seekBy(-(details && details.seekOffset ? details.seekOffset : 15)); },
      seekforward: function (details) { seekBy(details && details.seekOffset ? details.seekOffset : 15); },
      seekto: function (details) {
        if (details && typeof details.seekTime === "number") {
          seekToTime(details.seekTime);
          syncFromCurrentTime();
          updateMediaPositionState();
        }
      }
    };
    Object.keys(handlers).forEach(function (action) {
      try { navigator.mediaSession.setActionHandler(action, handlers[action]); }
      catch (err) { /* action unsupported in this browser */ }
    });
  }

  /* ---------- Storybook Illustration Stage (ONLY when hasScenes is true) ---------- */

  var storyRefs = null;
  var lightboxRefs = null;
  var preloadedImages = {};

  function preloadImage(url) {
    if (!url || preloadedImages[url]) { return; }
    preloadedImages[url] = true;
    var im = new Image();
    im.src = url;
  }

  function preloadChapterScenes(ch) {
    if (!hasScenes || !ch) { return; }
    preloadImage(coverSrc);
    (ch.scenes || []).forEach(function (sc) {
      if (sc.imageUrl) { preloadImage(sc.imageUrl); }
    });
  }

  function buildStoryStage() {
    if (!coverEl) { return; }
    panel.classList.add("has-story-stage");

    var stage = document.createElement("figure");
    stage.className = "story-stage";

    var frame = document.createElement("div");
    frame.className = "story-frame";

    var imgA = document.createElement("img");
    imgA.className = "story-img is-active";
    imgA.src = coverSrc;
    imgA.alt = coverAlt;

    var imgB = document.createElement("img");
    imgB.className = "story-img";
    imgB.alt = "";
    imgB.setAttribute("aria-hidden", "true");

    var expandBtn = document.createElement("button");
    expandBtn.type = "button";
    expandBtn.className = "story-expand-btn";
    expandBtn.textContent = "Full view";
    expandBtn.setAttribute("aria-label", "Open fullscreen bedtime illustration view");

    frame.appendChild(imgA);
    frame.appendChild(imgB);
    frame.appendChild(expandBtn);

    var captionBar = document.createElement("div");
    captionBar.className = "story-meta";
    var counter = document.createElement("span");
    counter.className = "story-counter";
    var caption = document.createElement("figcaption");
    caption.className = "story-caption";
    captionBar.appendChild(counter);
    captionBar.appendChild(caption);

    var dots = document.createElement("div");
    dots.className = "story-dots";
    dots.setAttribute("role", "group");
    dots.setAttribute("aria-label", "Chapter illustrations");

    stage.appendChild(frame);
    stage.appendChild(captionBar);
    stage.appendChild(dots);

    coverEl.replaceWith(stage);

    /* Create cozy dark Bedtime Lightbox (hidden by default). */
    var lightbox = document.createElement("div");
    lightbox.className = "story-lightbox";
    lightbox.hidden = true;
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.setAttribute("aria-label", bookTitle + " illustration viewer");

    var lbHeader = document.createElement("div");
    lbHeader.className = "lightbox-bar";
    var lbChapter = document.createElement("p");
    lbChapter.className = "lightbox-chapter";
    var lbClose = document.createElement("button");
    lbClose.type = "button";
    lbClose.className = "lightbox-close";
    lbClose.textContent = "Close";
    lbClose.setAttribute("aria-label", "Close fullscreen illustration view");
    lbHeader.appendChild(lbChapter);
    lbHeader.appendChild(lbClose);

    var lbBody = document.createElement("div");
    lbBody.className = "lightbox-body";
    var lbImg = document.createElement("img");
    lbImg.className = "lightbox-img";
    lbImg.src = coverSrc;
    lbImg.alt = coverAlt;
    var lbCaption = document.createElement("p");
    lbCaption.className = "lightbox-caption";
    lbBody.appendChild(lbImg);
    lbBody.appendChild(lbCaption);

    var lbControls = document.createElement("div");
    lbControls.className = "lightbox-controls";
    var lbPrev = document.createElement("button");
    lbPrev.type = "button";
    lbPrev.textContent = "← Prev ch";
    var lbBack15 = document.createElement("button");
    lbBack15.type = "button";
    lbBack15.textContent = "−15s";
    var lbPlay = document.createElement("button");
    lbPlay.type = "button";
    lbPlay.className = "lightbox-play";
    lbPlay.textContent = "Play";
    var lbFwd15 = document.createElement("button");
    lbFwd15.type = "button";
    lbFwd15.textContent = "+15s";
    var lbNext = document.createElement("button");
    lbNext.type = "button";
    lbNext.textContent = "Next ch →";
    lbControls.appendChild(lbPrev);
    lbControls.appendChild(lbBack15);
    lbControls.appendChild(lbPlay);
    lbControls.appendChild(lbFwd15);
    lbControls.appendChild(lbNext);

    lightbox.appendChild(lbHeader);
    lightbox.appendChild(lbBody);
    lightbox.appendChild(lbControls);
    document.body.appendChild(lightbox);

    storyRefs = {
      stage: stage,
      frame: frame,
      layers: [imgA, imgB],
      activeLayer: 0,
      caption: caption,
      counter: counter,
      dots: dots,
      expandBtn: expandBtn,
      currentImage: coverSrc
    };
    lightboxRefs = {
      root: lightbox,
      chapterEl: lbChapter,
      closeBtn: lbClose,
      img: lbImg,
      caption: lbCaption,
      prevBtn: lbPrev,
      nextBtn: lbNext,
      playBtn: lbPlay
    };

    function openLightbox() {
      lightbox.hidden = false;
      document.body.classList.add("lightbox-open");
      updatePlayLabels();
      lbClose.focus();
    }

    function closeLightbox() {
      lightbox.hidden = true;
      document.body.classList.remove("lightbox-open");
      expandBtn.focus();
    }

    expandBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      openLightbox();
    });
    frame.addEventListener("click", openLightbox);
    lbClose.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox || e.target === lbBody) { closeLightbox(); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !lightbox.hidden) { closeLightbox(); }
    });

    lbPrev.addEventListener("click", function () {
      if (current > 0) { selectChapter(current - 1, !player.paused); }
    });
    lbNext.addEventListener("click", function () {
      if (current + 1 < chapters.length) { selectChapter(current + 1, !player.paused); }
    });
    lbBack15.addEventListener("click", function () { seekBy(-15); });
    lbFwd15.addEventListener("click", function () { seekBy(15); });
    lbPlay.addEventListener("click", function () {
      if (player.paused || player.ended) { safePlay(); }
      else { player.pause(); }
    });
  }

  function updatePlayLabels() {
    if (!lightboxRefs) { return; }
    var playing = !player.paused && !player.ended;
    lightboxRefs.playBtn.textContent = playing ? "Pause" : "Play";
  }

  function crossfadeStage(imgUrl, altText) {
    if (!storyRefs) { return; }
    if (storyRefs.currentImage === imgUrl) { return; }
    var nextLayerIdx = storyRefs.activeLayer === 0 ? 1 : 0;
    var nextImg = storyRefs.layers[nextLayerIdx];
    var curImg = storyRefs.layers[storyRefs.activeLayer];
    nextImg.src = imgUrl;
    nextImg.alt = altText;
    nextImg.removeAttribute("aria-hidden");
    nextImg.classList.add("is-active");
    curImg.classList.remove("is-active");
    curImg.setAttribute("aria-hidden", "true");
    storyRefs.activeLayer = nextLayerIdx;
    storyRefs.currentImage = imgUrl;
  }

  function renderDots(ch, activeSceneIdx) {
    if (!storyRefs) { return; }
    var scenes = ch.scenes || [];
    if (!scenes.length) {
      storyRefs.dots.hidden = true;
      storyRefs.dots.replaceChildren();
      return;
    }
    storyRefs.dots.hidden = false;
    var buttons = [];

    function makeDot(label, isCurrent, targetChapterSec) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "story-dot";
      btn.textContent = label;
      if (isCurrent) { btn.setAttribute("aria-current", "true"); }
      btn.addEventListener("click", function () {
        var seekTarget = continuousMode
          ? (ch.startSeconds || 0) + targetChapterSec
          : targetChapterSec;
        seekToTime(seekTarget);
        syncFromCurrentTime();
        updateMediaPositionState();
        storageSave(true);
      });
      return btn;
    }

    buttons.push(makeDot("Cover", activeSceneIdx === -1, 0));
    scenes.forEach(function (sc, idx) {
      buttons.push(makeDot("Scene " + (idx + 1), activeSceneIdx === idx, sc.at_seconds));
    });
    storyRefs.dots.replaceChildren.apply(storyRefs.dots, buttons);
  }

  function updateSceneForTime(chapterIdx, chapterTime) {
    if (!hasScenes || !storyRefs) { return; }
    var ch = chapters[chapterIdx];
    if (!ch) { return; }
    var scenes = ch.scenes || [];
    var sceneIdx = -1;
    for (var i = 0; i < scenes.length; i += 1) {
      if (chapterTime + 0.2 >= scenes[i].at_seconds) { sceneIdx = i; }
    }
    var key = chapterIdx + ":" + sceneIdx;
    if (key === activeSceneKey) { return; }
    activeSceneKey = key;

    var imgUrl = sceneIdx >= 0 ? scenes[sceneIdx].imageUrl : coverSrc;
    var altText = sceneIdx >= 0 ? scenes[sceneIdx].alt : coverAlt;
    var captionText = sceneIdx >= 0
      ? scenes[sceneIdx].caption
      : (scenes.length
          ? "Illustration appears when the story reaches the scene."
          : "Listening with the book cover.");
    var countText = sceneIdx >= 0
      ? ("Scene " + (sceneIdx + 1) + " of " + scenes.length)
      : (scenes.length ? "Cover · " + scenes.length + (scenes.length === 1 ? " scene in chapter" : " scenes in chapter") : "Book cover");

    crossfadeStage(imgUrl, altText);
    storyRefs.caption.textContent = captionText;
    storyRefs.counter.textContent = countText;
    renderDots(ch, sceneIdx);

    if (lightboxRefs) {
      lightboxRefs.img.src = imgUrl;
      lightboxRefs.img.alt = altText;
      lightboxRefs.caption.textContent = sceneIdx >= 0 ? scenes[sceneIdx].caption : ch.title;
      lightboxRefs.chapterEl.textContent = "Chapter " + (chapterIdx + 1) + " of " + chapters.length + " · " + ch.title;
    }
    updateMediaMetadata();
  }

  function updateSceneForCurrentChapter() {
    if (!hasScenes) { return; }
    var t = pendingSeek !== null ? pendingSeek : (player.currentTime || 0);
    var chTime = continuousMode ? Math.max(0, t - (chapters[current].startSeconds || 0)) : t;
    updateSceneForTime(current, chTime);
  }

  function syncFromCurrentTime() {
    var t = pendingSeek !== null ? pendingSeek : (player.currentTime || 0);
    if (continuousMode) {
      var chIdx = chapterIndexForBookTime(t);
      if (chIdx !== current) {
        setActiveChapterUI(chIdx);
        updateMediaMetadata();
      }
      updateSceneForTime(chIdx, Math.max(0, t - (chapters[chIdx].startSeconds || 0)));
    } else {
      updateSceneForTime(current, t);
    }
  }

  /* ---------- Audio Element Event Wiring ---------- */

  player.addEventListener("loadedmetadata", function () {
    if (pendingSeek !== null) {
      var target = pendingSeek;
      pendingSeek = null;
      var maxDur = isFinite(player.duration) && player.duration > 0 ? player.duration : target;
      try { player.currentTime = Math.min(maxDur, Math.max(0, target)); } catch (err) { /* keep */ }
    }
    syncFromCurrentTime();
    updateMediaPositionState();
  });

  player.addEventListener("timeupdate", function () {
    syncFromCurrentTime();
    var now = Date.now();
    if (now - lastPositionStateAt >= 1000) {
      lastPositionStateAt = now;
      updateMediaPositionState();
    }
    if (!player.paused) { storageSave(false); }
  });

  player.addEventListener("seeked", function () {
    syncFromCurrentTime();
    updateMediaPositionState();
    storageSave(true);
  });

  player.addEventListener("play", function () {
    statusEl.textContent = "";
    if (!continuousMode) { preloadTrack(current + 1); }
    if ("mediaSession" in navigator) {
      try { navigator.mediaSession.playbackState = "playing"; } catch (err) {}
    }
    updatePlayLabels();
    updateMediaPositionState();
  });

  player.addEventListener("pause", function () {
    if ("mediaSession" in navigator) {
      try { navigator.mediaSession.playbackState = "paused"; } catch (err) {}
    }
    updatePlayLabels();
    updateMediaPositionState();
    storageSave(true);
  });

  player.addEventListener("ended", function () {
    updatePlayLabels();
    if (!continuousMode && current + 1 < chapters.length) {
      selectChapter(current + 1, true);
      return;
    }
    statusEl.textContent = "You have reached the end of the book.";
    storageSave(true);
  });

  player.addEventListener("error", function () {
    statusEl.textContent = "This audio track could not be played. Try again or choose another chapter.";
    updatePlayLabels();
  });

  if (previousBtn) {
    previousBtn.addEventListener("click", function () {
      if (current > 0) { selectChapter(current - 1, !player.paused); }
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      if (current + 1 < chapters.length) { selectChapter(current + 1, !player.paused); }
    });
  }

  /* ---------- Bootstrap from chapters.json (with graceful fallback) ---------- */

  function finalizeStartup(manifest) {
    if (manifest && Array.isArray(manifest.chapters)) {
      var byNum = {};
      manifest.chapters.forEach(function (entry) { byNum[entry.number] = entry; });
      chapters.forEach(function (ch) {
        var m = byNum[ch.number];
        if (!m) { return; }
        ch.seconds = m.seconds || 0;
        if (typeof m.start_seconds === "number") { ch.startSeconds = m.start_seconds; }
        ch.scenes = (m.scenes || []).map(function (sc) {
          return {
            id: sc.id,
            at_seconds: Number(sc.at_seconds) || 0,
            book_seconds: Number(sc.book_seconds) || 0,
            imageUrl: sc.image ? new URL(sc.image, chaptersJsonUrl).href : coverSrc,
            caption: sc.caption || "",
            alt: sc.alt || coverAlt
          };
        });
        if (ch.scenes.length) { hasScenes = true; }
      });

      if (manifest.full_book && manifest.full_book.file && chapters.length > 1) {
        fullBookUrl = new URL(manifest.full_book.file, chaptersJsonUrl).href;
        totalDuration = Number(manifest.full_book.seconds) || Number(manifest.total_seconds) || 0;
        continuousMode = true;
        player.src = fullBookUrl;
        if (linksContainer && !panel.querySelector("[data-full-download]")) {
          var fullLink = document.createElement("a");
          fullLink.href = fullBookUrl;
          fullLink.download = "";
          fullLink.setAttribute("data-full-download", "true");
          fullLink.textContent = "Download full book";
          if (downloadLink && downloadLink.nextSibling) {
            linksContainer.insertBefore(fullLink, downloadLink.nextSibling);
          } else {
            linksContainer.appendChild(fullLink);
          }
        }
        if (hintEl) {
          hintEl.textContent = "Plays continuously across all chapters, even with your screen locked.";
        }
      }
    }

    if (hasScenes) { buildStoryStage(); }
    initMediaSessionHandlers();

    var saved = storageGet();
    if (continuousMode) {
      var startTime = (saved && saved.mode === "full" && typeof saved.time === "number" && saved.time > 2)
        ? saved.time
        : 0;
      var startCh = chapterIndexForBookTime(startTime);
      setActiveChapterUI(startCh);
      if (startTime > 0) { seekToTime(startTime); }
      updateSceneForTime(startCh, Math.max(0, startTime - (chapters[startCh].startSeconds || 0)));
      updateMediaMetadata();
    } else {
      var startIdx = (saved && typeof saved.chapter === "number" && saved.chapter >= 0 && saved.chapter < chapters.length)
        ? saved.chapter
        : 0;
      selectChapter(startIdx, false);
      if (saved && saved.mode === "track" && typeof saved.time === "number" && saved.time > 2) {
        seekToTime(saved.time);
      }
    }
    panel.hidden = false;
  }

  fetch(chaptersJsonUrl).then(function (resp) {
    if (!resp.ok) { throw new Error("chapters manifest HTTP " + resp.status); }
    return resp.json();
  }).then(function (manifest) {
    finalizeStartup(manifest);
  }).catch(function () {
    finalizeStartup(null);
  });
}());
