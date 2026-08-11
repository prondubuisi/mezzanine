(function () {
    function csrfToken() {
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    document.body.addEventListener("htmx:configRequest", function (event) {
        var token = csrfToken();
        if (token) {
            event.detail.headers["X-CSRFToken"] = token;
        }
    });

    document.body.addEventListener("htmx:beforeSwap", function (event) {
        if (event.detail.xhr && event.detail.xhr.status === 400) {
            event.detail.shouldSwap = true;
            event.detail.isError = false;
        }
    });

    var cookieName = "mezzanine-admin-toolbar";
    var cookieValue = "1";
    var toolbar = document.getElementById("editable-toolbar");
    if (!toolbar) {
        return;
    }
    var toggle = document.getElementById("editable-toolbar-toggle");
    var extras = Array.prototype.filter.call(toolbar.children, function (el) {
        return el.id !== "editable-toolbar-toggle";
    });

    function toolbarOpen() {
        var at = ("; " + document.cookie).indexOf("; " + cookieName + "=");
        if (at > -1) {
            at += cookieName.length + 1;
            return document.cookie.substr(at).split(";")[0] === cookieValue;
        }
        return null;
    }

    function setHidden(hide) {
        extras.forEach(function (el) {
            el.style.display = hide ? "none" : "";
        });
        document.querySelectorAll(".editable-edit").forEach(function (el) {
            el.style.visibility = hide ? "hidden" : "visible";
        });
        if (toggle) {
            toggle.textContent = hide ? "»" : "«";
        }
        document.cookie = hide
            ? cookieName + "=" + cookieValue + "; path=/"
            : cookieName + "=; path=/";
    }

    toolbar.style.display = "block";
    setHidden(toolbarOpen() !== false);
    if (toggle) {
        toggle.addEventListener("click", function (event) {
            event.preventDefault();
            setHidden(!toolbarOpen());
        });
    }
})();
