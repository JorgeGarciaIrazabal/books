(function () {
  "use strict";
  var rows = Array.from(document.querySelectorAll(".chapter-audio li"));
  var panel = document.getElementById("audio-player");
  if (!panel || !rows.length) { return; }
  var control = document.getElementById("audio-control");
  var title = document.getElementById("audio-current");
  var position = document.getElementById("audio-position");
  var status = document.getElementById("audio-status");
  var previous = document.getElementById("audio-previous");
  var next = document.getElementById("audio-next");
  var download = document.getElementById("audio-download");
  var current = 0;
  var chapters = rows.map(function (row, index) {
    var heading = row.querySelector("h3");
    var audio = row.querySelector("audio");
    audio.remove();
    var button = document.createElement("button");
    button.type = "button";
    button.className = "chapter-select";
    var chapterTitle = heading.textContent;
    button.textContent = chapterTitle.replace(/^Chapter [^:]+: /, "");
    button.setAttribute("aria-label", chapterTitle);
    var details = row.querySelector("p");
    var link = details.querySelector("a");
    var downloadHref = link.href;
    link.hidden = true;
    heading.replaceWith(button);
    button.addEventListener("click", function () { select(index, !chapters[current].audio.paused); });
    audio.addEventListener("ended", function () {
      if (index !== current) { return; }
      if (index + 1 < chapters.length) { select(index + 1, true); }
      else { status.textContent = "You have reached the end of the book."; }
    });
    audio.addEventListener("error", function () {
      if (index === current) { status.textContent = "This chapter could not be played. Try again or choose another chapter."; }
    });
    return { audio: audio, button: button, title: chapterTitle, download: downloadHref };
  });
  function select(index, play) {
    var old = chapters[current].audio;
    old.pause();
    if (index !== current) { old.currentTime = 0; }
    current = index;
    var chapter = chapters[index];
    control.replaceChildren(chapter.audio);
    title.textContent = chapter.title;
    download.href = chapter.download;
    position.textContent = "Chapter " + (index + 1) + " of " + chapters.length;
    chapters.forEach(function (item, i) {
      if (i === index) { item.button.setAttribute("aria-current", "true"); }
      else { item.button.removeAttribute("aria-current"); }
    });
    previous.disabled = index === 0;
    next.disabled = index === chapters.length - 1;
    status.textContent = "";
    if (play) {
      var promise = chapter.audio.play();
      if (promise && promise.catch) {
        promise.catch(function () {
          if (current === index) { status.textContent = "Press play to continue listening."; }
        });
      }
    }
  }
  previous.addEventListener("click", function () { select(current - 1, !chapters[current].audio.paused); });
  next.addEventListener("click", function () { select(current + 1, !chapters[current].audio.paused); });
  select(0, false);
  panel.hidden = false;
}());
