/* Demo now-playing bar — no real audio. */
(function () {
  var playing = false;
  var timer = null;
  var elapsed = 0;
  var durationSec = 180;

  function $(id) {
    return document.getElementById(id);
  }

  function parseDuration(text) {
    if (!text) return 180;
    var parts = String(text).split(":");
    if (parts.length !== 2) return 180;
    return (parseInt(parts[0], 10) || 0) * 60 + (parseInt(parts[1], 10) || 0);
  }

  function format(sec) {
    sec = Math.max(0, Math.floor(sec));
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  function setPlaying(on) {
    playing = on;
    var btn = $("np-play");
    if (btn) {
      btn.textContent = on ? "❚❚" : "▶";
      btn.setAttribute("aria-label", on ? "Pause" : "Play");
      btn.classList.toggle("is-playing", on);
    }
    if (on) {
      if (timer) clearInterval(timer);
      timer = setInterval(function () {
        elapsed += 1;
        if (elapsed >= durationSec) {
          elapsed = durationSec;
          setPlaying(false);
        }
        var el = $("np-elapsed");
        var fill = $("np-fill");
        if (el) el.textContent = format(elapsed);
        if (fill) fill.style.width = (elapsed / durationSec) * 100 + "%";
      }, 1000);
    } else if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function playFromDataset(el) {
    if (!el || !el.dataset.playTitle) return;
    var title = el.dataset.playTitle;
    var artist = el.dataset.playArtist || "";
    var duration = el.dataset.playDuration || "3:00";
    var cover = el.dataset.playCover || "violet";
    var t = $("np-title");
    var a = $("np-artist");
    var d = $("np-duration");
    var c = $("np-cover");
    if (t) t.textContent = title;
    if (a) a.innerHTML = artist;
    if (d) d.textContent = duration;
    if (c) {
      c.className = "sp-cover sp-cover-sm cover-" + cover;
    }
    durationSec = parseDuration(duration);
    elapsed = 0;
    var elap = $("np-elapsed");
    var fill = $("np-fill");
    if (elap) elap.textContent = "0:00";
    if (fill) fill.style.width = "0%";
    setPlaying(true);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var playBtn = $("np-play");
    if (playBtn) {
      playBtn.addEventListener("click", function () {
        setPlaying(!playing);
      });
    }
    document.body.addEventListener("click", function (ev) {
      var target = ev.target.closest("[data-play-title]");
      if (!target) return;
      if (target.tagName === "A") return;
      playFromDataset(target);
    });
    document.body.addEventListener("keydown", function (ev) {
      if (ev.key !== "Enter" && ev.key !== " ") return;
      var target = ev.target.closest("tr[data-play-title]");
      if (!target) return;
      ev.preventDefault();
      playFromDataset(target);
    });
  });
})();
