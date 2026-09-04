// Load /data/stats.json and populate the #bil-stats section, if present.
// Fetched same-origin (no CORS needed). Cache disabled - the JSON is
// regenerated daily and we want the browser to pick up updates.
(function () {
  "use strict";

  function fmt(n) {
    return typeof n === "number" ? n.toLocaleString("en-US") : "-";
  }

  function fillHeadline(headline) {
    document.querySelectorAll("#bil-stat-grid [data-stat]").forEach(function (el) {
      var key = el.getAttribute("data-stat");
      var value;
      if (key === "datasets-rounded") {
        // Round DOWN to the nearest thousand for the "14,000+" style panel.
        var n = headline.datasets;
        value = typeof n === "number" ? Math.floor(n / 1000) * 1000 : null;
      } else {
        value = headline[key];
      }
      el.textContent = fmt(value);
    });
  }

  function renderBars(containerId, rows) {
    var container = document.getElementById(containerId);
    if (!container || !rows || !rows.length) return;
    var max = rows.reduce(function (m, r) { return r.count > m ? r.count : m; }, 0);
    if (max === 0) return;
    var html = rows.map(function (r) {
      var pct = (r.count / max) * 100;
      return (
        '<div class="bar-row">' +
          '<span class="bar-name">' + r.name + '</span>' +
          '<div class="bar-track"><div class="bar-fill" style="width:' + pct.toFixed(1) + '%"></div></div>' +
          '<span class="bar-count">' + fmt(r.count) + '</span>' +
        '</div>'
      );
    }).join("");
    container.innerHTML = html;
  }

  async function loadStats() {
    var host = document.getElementById("bil-stats");
    if (!host) return;
    try {
      var resp = await fetch("/data/stats.json", { cache: "no-store" });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      var data = await resp.json();
      fillHeadline(data.headline);
      renderBars("bil-species-bars", data.species);
      renderBars("bil-modality-bars", data.modalities);
    } catch (e) {
      console.warn("BIL stats load failed:", e);
      host.classList.add("bil-stats--unavailable");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStats);
  } else {
    loadStats();
  }
})();
