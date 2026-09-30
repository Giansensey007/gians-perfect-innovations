(function () {
  const G = window.GPI;
  const app = document.getElementById("app");
  const slug = location.pathname.replace(/^\/innovation\/?/, "").replace(/\/$/, "");

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function row(label, value) {
    if (!value) return "";
    return (
      '<div class="pw-row"><span class="pw-label">' + G.escapeHtml(label) + "</span><span>" +
      G.escapeHtml(value) + "</span></div>"
    );
  }

  function notFound() {
    app.innerHTML =
      '<a class="back-link" href="/">Back to listings</a>' +
      "<h1>Not found</h1>" +
      '<p class="lede">That innovation is not in this catalog.</p>';
  }

  app.innerHTML = '<p class="waiting">Loading</p>';

  G.loadCatalog()
    .then(function (catalog) {
      const idea = (catalog.ideas || []).find(function (item) {
        return item.slug === slug;
      });
      if (!idea) {
        notFound();
        return;
      }
      render(idea);
    })
    .catch(function (err) {
      app.innerHTML =
        '<a class="back-link" href="/">Back to listings</a>' +
        '<p class="lede">' + G.escapeHtml(err.message) + "</p>";
    });

  function render(idea) {
    const images = (idea.images || []).filter(function (image) {
      return G.safeMedia(image.src);
    });
    const vt = "idea-" + String(idea.slug || "").replace(/[^a-z0-9-]/g, "");
    const claims = (idea.claims || []).map(function (claim) {
      return "<li>" + G.escapeHtml(claim) + "</li>";
    }).join("");
    const patentUrl = G.safeHttp(idea.patentUrl);
    const espacenetUrl = G.safeHttp(idea.espacenetUrl);
    document.title = idea.name + " | Gian's Perfect Innovations";

    app.innerHTML =
      '<a class="back-link" href="/">Back to listings</a>' +
      '<p class="kicker">' + G.escapeHtml(idea.category || "") + "</p>" +
      "<h1>" + G.escapeHtml(idea.name) + "</h1>" +
      '<div class="facts-strip">' +
      '<span class="meta">Patent <strong>' + G.escapeHtml(idea.patentNumber || "-") + "</strong></span>" +
      '<span class="meta">Filed <strong>' + G.escapeHtml(idea.filing || "-") + "</strong></span>" +
      '<span class="meta">Abandoned <strong>' + G.escapeHtml(idea.abandonDate || "-") + "</strong></span>" +
      '<span class="meta">Status <strong>Never granted</strong></span>' +
      "</div>" +
      '<div class="diashow">' +
      '<div class="photo-frame diashow-main"><img id="hero" alt="" style="view-transition-name:' + vt + '"></div>' +
      '<div class="diashow-bar"><span class="diashow-count" id="count"></span>' +
      '<span class="diashow-nav">' +
      '<button type="button" class="icon-btn" id="prev">Prev</button>' +
      '<button type="button" class="icon-btn" id="next">Next</button>' +
      "</span></div>" +
      '<div class="thumbs" id="thumbs">' +
      images.map(function (image, index) {
        return (
          '<button type="button" data-idx="' + index + '" aria-label="Image ' + (index + 1) + '">' +
          '<img src="' + G.escapeHtml(image.src) + '" alt="">' +
          "</button>"
        );
      }).join("") +
      "</div></div>" +
      (idea.pitch ? '<p class="lede">' + G.escapeHtml(idea.pitch) + "</p>" : "") +
      '<div class="split-notes">' +
      '<section class="note-block"><p class="kicker">Upgrade vs original</p><p>' + G.escapeHtml(idea.upgrade || "No upgrade notes.") + "</p></section>" +
      '<section class="note-block"><p class="kicker">Why now</p><p>' + G.escapeHtml(idea.whyNow || "No timing notes.") + "</p></section>" +
      "</div>" +
      '<section class="value-panel"><p class="kicker">Next build</p><p class="next-copy">' + G.escapeHtml(idea.next || "") + "</p></section>" +
      '<section class="section"><p class="kicker">Target user</p><p class="lede">' + G.escapeHtml(idea.target || "") + "</p></section>" +
      '<section class="section"><p class="kicker">Original filing</p><div class="meta-rows">' +
      row("Title", idea.patentTitle) +
      row("Inventor", idea.inventor) +
      row("Assignee", idea.assignee) +
      row("Application", idea.app) +
      row("Published", idea.publication) +
      row("Status", idea.status) +
      "</div>" +
      (claims ? '<p class="kicker" style="margin-top:1.1rem">Paraphrased claims</p><ol class="claims">' + claims + "</ol>" : "") +
      "</section>" +
      (idea.fto ? '<section class="section"><p class="kicker">Freedom to operate</p><p>' + G.escapeHtml(idea.fto) + "</p></section>" : "") +
      '<div class="actions">' +
      (patentUrl ? '<a class="btn" href="' + G.escapeHtml(patentUrl) + '" target="_blank" rel="noopener noreferrer">Read on Google Patents</a>' : "") +
      (espacenetUrl ? '<a class="btn btn-outline" href="' + G.escapeHtml(espacenetUrl) + '" target="_blank" rel="noopener noreferrer">Espacenet</a>' : "") +
      "</div>";

    let idx = 0;
    const hero = document.getElementById("hero");
    const count = document.getElementById("count");
    const thumbButtons = Array.prototype.slice.call(app.querySelectorAll(".thumbs button"));

    function show(next) {
      if (!images.length) {
        count.textContent = "00 / 00";
        return;
      }
      idx = (next + images.length) % images.length;
      const image = images[idx];
      hero.src = image.src;
      hero.alt = image.alt || idea.name;
      count.textContent = pad(idx + 1) + " / " + pad(images.length);
      thumbButtons.forEach(function (button, index) {
        if (index === idx) button.setAttribute("aria-current", "true");
        else button.removeAttribute("aria-current");
      });
    }

    document.getElementById("prev").onclick = function () { show(idx - 1); };
    document.getElementById("next").onclick = function () { show(idx + 1); };
    thumbButtons.forEach(function (button) {
      button.onclick = function () { show(Number(button.getAttribute("data-idx"))); };
    });
    document.onkeydown = function (event) {
      if (event.key === "ArrowLeft") show(idx - 1);
      if (event.key === "ArrowRight") show(idx + 1);
    };
    show(0);
  }
})();
