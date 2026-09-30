(function () {
  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function safeMedia(src) {
    return typeof src === "string" && src.startsWith("/media/") ? src : "";
  }

  function safeHttp(url) {
    return typeof url === "string" && /^https:\/\//.test(url) ? url : "";
  }

  let catalogPromise = null;
  function loadCatalog() {
    if (!catalogPromise) {
      catalogPromise = fetch("/data/catalog.json").then(function (res) {
        if (!res.ok) throw new Error("Catalog failed to load");
        return res.json();
      });
    }
    return catalogPromise;
  }

  function familyLabel(family) {
    if (!family) return "Other";
    return family.charAt(0).toUpperCase() + family.slice(1);
  }

  window.GPI = {
    escapeHtml: escapeHtml,
    safeMedia: safeMedia,
    safeHttp: safeHttp,
    loadCatalog: loadCatalog,
    familyLabel: familyLabel,
  };
})();
