/**
 * Nova media chooser for FileField admin widgets (no filebrowser).
 * Opens /_nova/media/chooser/ and writes storage path into *_nova_path.
 */
(function () {
  "use strict";

  function chooserBase() {
    return (
      window.__nova_media_chooser_url ||
      window.__filebrowser_url ||
      "/_nova/media/chooser/"
    );
  }

  function openChooser(pathInput, preview) {
    var base = chooserBase();
    if (!base) {
      return;
    }
    var fieldId = pathInput.id;
    var sep = base.indexOf("?") >= 0 ? "&" : "?";
    var src =
      base +
      sep +
      "field=" +
      encodeURIComponent(fieldId) +
      "&mode=path";
    window.open(
      src,
      "novaMedia",
      "width=840,height=560,resizable=yes,scrollbars=yes"
    );
  }

  function bind(root) {
    if (!root || root.getAttribute("data-nova-bound")) {
      return;
    }
    root.setAttribute("data-nova-bound", "1");
    var pathInput = root.querySelector(".nova-media-path");
    var browse = root.querySelector(".nova-media-browse");
    var clearBtn = root.querySelector(".nova-media-clear-library");
    var preview = root.querySelector(".nova-media-preview");
    if (!pathInput || !browse) {
      return;
    }
    browse.addEventListener("click", function (e) {
      e.preventDefault();
      openChooser(pathInput, preview);
    });
    if (clearBtn) {
      clearBtn.addEventListener("click", function (e) {
        e.preventDefault();
        pathInput.value = "";
        if (preview) {
          preview.style.display = "none";
          preview.innerHTML = "";
        }
        clearBtn.style.display = "none";
      });
    }
  }

  function scan(ctx) {
    (ctx || document)
      .querySelectorAll(".nova-media-chooser-widget")
      .forEach(bind);
  }

  // Called by media_chooser.html when mode=path and field id matches.
  window.novaMediaFieldSelected = function (fieldId, path, url, alt) {
    var pathInput = document.getElementById(fieldId);
    if (!pathInput) {
      return;
    }
    pathInput.value = path || "";
    var root = pathInput.closest(".nova-media-chooser-widget");
    if (!root) {
      return;
    }
    var preview = root.querySelector(".nova-media-preview");
    var clearBtn = root.querySelector(".nova-media-clear-library");
    if (preview) {
      preview.style.display = path ? "" : "none";
      if (path) {
        var img = url
          ? '<img src="' +
            url.replace(/"/g, "&quot;") +
            '" alt="" class="nova-media-thumb">'
          : "";
        preview.innerHTML =
          img +
          '<span class="nova-media-path-label">' +
          (path || "").replace(/</g, "&lt;") +
          "</span>";
      } else {
        preview.innerHTML = "";
      }
    }
    if (clearBtn) {
      clearBtn.style.display = path ? "" : "none";
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      scan();
    });
  } else {
    scan();
  }
  document.addEventListener("formset:added", function (e) {
    scan(e.target);
  });
})();
