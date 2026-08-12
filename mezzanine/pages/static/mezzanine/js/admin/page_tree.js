/**
 * Page tree admin (PR-029).
 *
 * Uses jQuery UI Sortable with connectWith for nested reordering.
 * Vendor tree-plugin removed (PR-029). Still POSTs to admin_page_ordering.
 */
jQuery(function ($) {
    var cookie = "mezzanine-admin-tree";
    var at = ("; " + document.cookie).indexOf("; " + cookie + "=");
    var ids = "";

    if (at > -1) {
        ids = document.cookie.substr(at + cookie.length + 1).split(";")[0];
    }

    var toggleID = function (opened, id) {
        var index = $.inArray(id, ids.split(","));
        if (opened) {
            if (index === -1) {
                if (ids) {
                    ids += ",";
                }
                ids += id;
            }
        } else if (index > -1) {
            ids = ids.split(",");
            ids.splice(index, 1);
            ids = ids.join(",");
        }
        document.cookie = cookie + "=" + ids + "; path=/";
    };

    function showButtonWithChildren() {
        $("li:has(li) .tree-toggle").css({ visibility: "visible" });
        $("li:not(:has(li)) .tree-toggle").css({ visibility: "hidden" });
    }

    showButtonWithChildren();

    if (window.__grappelli_installed) {
        $(".delete").addClass("grappelli-delete");
    }

    $("#tree .tree-toggle").click(function () {
        var pageLink = $(this);
        pageLink.parent().parent().find("ol:first").toggle();
        pageLink.find(".icon").toggle();
        var opened = pageLink.find(".close:visible").length === 1;
        var id = pageLink.attr("id").split("-")[1];
        toggleID(opened, id);
        return false;
    });

    $("#tree ol").find("ol").hide();
    if (ids) {
        $("#page-" + ids.split(",").join(", #page-")).each(function () {
            var pageLink = $(this);
            pageLink.parent().parent().find("ol:first").toggle();
            pageLink.find(".close").css("display", "inline");
            pageLink.find(".open").css("display", "none");
        });
    }

    $(".addlist").change(function () {
        var id = $(this).attr("id");
        if (id) {
            toggleID(true, id.split("-")[1]);
        }
    });

    var updateOrdering = function (event, ui) {
        var parent = ui.item.parents("li:first");
        var args = {
            id: ui.item[0].id,
            parent_id: parent.length ? parent[0].id : "null",
            siblings: ui.item
                .parent()
                .children()
                .map(function (index, elem) {
                    return elem.id;
                })
                .get(),
        };

        $.post(window.__page_ordering_url, args, function (data) {
            if (String(data).substr(0, 2) !== "ok") {
                location.reload();
            } else {
                $(".messagelist").remove();
            }
        });

        showButtonWithChildren();
    };

    // Nested reordering via jQuery UI Sortable only (no nestedSortable).
    $("#tree ol").sortable({
        handle: ".ordering",
        opacity: 0.5,
        stop: updateOrdering,
        forcePlaceholderSize: true,
        placeholder: "placeholder",
        revert: 150,
        helper: "clone",
        items: "> li",
        tolerance: "pointer",
        connectWith: "#tree ol",
        dropOnEmpty: true,
    });
});
