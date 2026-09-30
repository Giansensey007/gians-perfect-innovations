(function () {
  const G = window.GPI;
  const grid = document.getElementById("grid");
  const toolbar = document.getElementById("toolbar");
  let ideas = [];
  let family = "";

  function families(rows) {
    const seen = [];
    rows.forEach(function (idea) {
      if (idea.family && seen.indexOf(idea.family) === -1) seen.push(idea.family);
    });
    return seen;
  }

  function card(idea) {
    const cover = (idea.images || []).find(function (image) {
      return image.kind === "photoreal";
    }) || (idea.images || [])[0];
    const src = cover ? G.safeMedia(cover.src) : "";
    const vt = "idea-" + String(idea.slug || "").replace(/[^a-z0-9-]/g, "");
    const img = src
      ? '<img src="' + G.escapeHtml(src) + '" alt="' + G.escapeHtml(cover.alt || idea.name) + '" width="1280" height="720" style="view-transition-name:' + vt + '">'
      : "";
    const href = "/innovation/" + encodeURIComponent(idea.slug);
    return (
      '<a class="listing-card" href="' + href + '">' +
      '<p class="kicker">' + G.escapeHtml(idea.category || "") + "</p>" +
      '<div class="photo-frame">' + img + "</div>" +
      "<h2>" + G.escapeHtml(idea.name) + "</h2>" +
      '<p class="card-pitch">' + G.escapeHtml(idea.cardPitch || idea.pitch || "") + "</p>" +
      '<p class="card-meta">' + G.escapeHtml(idea.patentNumber || "") + "</p>" +
      "</a>"
    );
  }

  function render() {
    const rows = ideas.filter(function (idea) {
      return !family || idea.family === family;
    });
    if (!rows.length) {
      grid.innerHTML = '<p class="empty">No innovations in this field.</p>';
      return;
    }
    grid.innerHTML = rows.map(card).join("");
  }

  function paintToolbar() {
    const options = [{ id: "", label: "All" }].concat(
      families(ideas).map(function (id) {
        return { id: id, label: G.familyLabel(id) };
      })
    );
    toolbar.innerHTML =
      '<div class="toolbar-row"><span class="toolbar-label">Field</span><div class="seg">' +
      options.map(function (option) {
        const pressed = family === option.id;
        return (
          '<button type="button" data-family="' + G.escapeHtml(option.id) + '" aria-pressed="' + pressed + '">' +
          G.escapeHtml(option.label) +
          "</button>"
        );
      }).join("") +
      "</div></div>";
  }

  toolbar.addEventListener("click", function (event) {
    const button = event.target.closest("button[data-family]");
    if (!button) return;
    family = button.getAttribute("data-family") || "";
    toolbar.querySelectorAll("button[data-family]").forEach(function (item) {
      item.setAttribute("aria-pressed", String(item === button));
    });
    render();
  });

  grid.innerHTML = '<p class="waiting">Loading</p>';
  G.loadCatalog()
    .then(function (catalog) {
      ideas = catalog.ideas || [];
      paintToolbar();
      render();
    })
    .catch(function (err) {
      grid.innerHTML = '<p class="empty">' + G.escapeHtml(err.message) + "</p>";
    });
})();
