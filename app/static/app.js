"use strict";

const $ = (sel) => document.querySelector(sel);
const fmtUsd = (n) => "$" + Number(n || 0).toFixed(6);
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

// --- Tabs --------------------------------------------------------------------
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $("#panel-" + tab.dataset.tab).classList.add("active");
    if (tab.dataset.tab === "metrics") refreshMetrics();
  });
});

// --- Example chips -----------------------------------------------------------
const EXAMPLES = [
  "how are sales trending?",
  "which product is selling the most?",
  "compare sales by region",
  "show me revenue anomalies",
  "forecast next week revenue",
  "what is the worst performing product?",
];
const chips = $("#chips-analyze");
EXAMPLES.forEach((ex) => {
  const b = document.createElement("button");
  b.className = "chip";
  b.textContent = ex;
  b.onclick = () => { $("#q-analyze").value = ex; runAnalyze(); };
  chips.appendChild(b);
});

// --- Health ------------------------------------------------------------------
async function refreshHealth() {
  try {
    const r = await fetch("/health");
    const h = await r.json();
    $("#health-dot").className = "dot " + h.status;
    $("#health-text").textContent =
      h.status + " · v" + h.version + (h.providers_available.length ? " · " + h.providers_available.join(",") : "");
  } catch {
    $("#health-dot").className = "dot error";
    $("#health-text").textContent = "offline";
  }
}

// --- Single analysis ---------------------------------------------------------
async function runAnalyze() {
  const query = $("#q-analyze").value.trim();
  if (!query) return;
  const btn = $("#btn-analyze");
  btn.disabled = true;
  $("#analyze-out").innerHTML = '<div class="empty"><span class="spinner"></span> Analyzing…</div>';
  try {
    const r = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    renderAnalyze(d);
  } catch (e) {
    $("#analyze-out").innerHTML = `<div class="card"><span class="muted">Error: ${esc(e.message)}</span></div>`;
  } finally {
    btn.disabled = false;
  }
}

function renderAnalyze(d) {
  const chart = chartForResult(d.task, d.result);
  $("#analyze-out").innerHTML = `
    <div class="grid cols-2">
      <div class="card">
        <h3>${esc(d.task)} · insight</h3>
        <div class="insight">${esc(d.insight)}</div>
        <div class="kv">
          <span>model <b>${esc(d.model_used)}</b></span>
          <span>provider <b>${esc(d.provider_used || "rule-based")}</b></span>
          <span>latency <b>${d.latency_ms} ms</b></span>
          <span>tokens <b>${d.tokens}</b></span>
          <span>cost <b>${fmtUsd(d.cost_usd)}</b></span>
          <span>trace <b><a href="/traces/${esc(d.trace_id)}" target="_blank">${esc((d.trace_id||"").slice(0,8))}</a></b></span>
        </div>
      </div>
      <div class="card">
        <h3>Result data</h3>
        ${chart ? '<canvas id="result-chart" height="170"></canvas>' : `<pre class="insight" style="font-size:13px">${esc(JSON.stringify(d.result, null, 2))}</pre>`}
      </div>
    </div>`;
  if (chart) chart();
}

// --- Multi-agent consensus ---------------------------------------------------
async function runConsensus() {
  const query = $("#q-consensus").value.trim();
  if (!query) return;
  const btn = $("#btn-consensus");
  btn.disabled = true;
  $("#consensus-out").innerHTML = '<div class="empty"><span class="spinner"></span> Convening the agent panel…</div>';
  try {
    const r = await fetch("/analyze/consensus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    renderConsensus(await r.json());
  } catch (e) {
    $("#consensus-out").innerHTML = `<div class="card"><span class="muted">Error: ${esc(e.message)}</span></div>`;
  } finally {
    btn.disabled = false;
  }
}

function renderConsensus(d) {
  const cards = d.findings
    .map((f) => {
      const pct = Math.round(f.confidence * 100);
      return `
      <div class="card agent-card ${esc(f.role)}">
        <div class="agent-head">
          <span class="name">${esc(f.agent)}</span>
          <span class="badge ${f.source === "llm" ? "llm" : ""}">${esc(f.source)}</span>
        </div>
        <div class="insight" style="font-size:14px">${esc(f.insight)}</div>
        <div class="confbar"><i style="width:${pct}%"></i></div>
        <div class="sub">confidence ${pct}%</div>
      </div>`;
    })
    .join("");

  const v = d.reconciled;
  const conflicts = (v.conflicts || [])
    .map((c) => `<div class="conflict">⚠ ${esc(c)}</div>`)
    .join("");
  $("#consensus-out").innerHTML = `
    <div class="grid cols-3">${cards}</div>
    <div class="card verdict" style="margin-top:16px">
      <div class="agent-head">
        <span class="name">🧭 Reconciled Verdict</span>
        <span class="badge ${v.source === "llm" ? "llm" : ""}">${esc(v.source)} · ${Math.round(v.confidence*100)}%</span>
      </div>
      <div class="insight">${esc(v.insight)}</div>
      ${conflicts || '<div class="sub" style="margin-top:8px">No conflicts detected — signals are consistent.</div>'}
      <div class="kv"><span>agents <b>${d.agent_count}</b></span><span>trace <b><a href="/traces/${esc(d.trace_id)}" target="_blank">${esc((d.trace_id||"").slice(0,8))}</a></b></span></div>
    </div>`;
}

// --- Live stream (SSE over fetch) -------------------------------------------
async function runStream() {
  const query = $("#q-stream").value.trim();
  if (!query) return;
  const log = $("#stream-log");
  log.textContent = "";
  const btn = $("#btn-stream");
  btn.disabled = true;
  try {
    const r = await fetch("/analyze/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const events = buf.split("\n\n");
      buf = events.pop();
      for (const block of events) {
        const evLine = block.split("\n").find((l) => l.startsWith("event:")) || "";
        const dataLine = block.split("\n").find((l) => l.startsWith("data:")) || "";
        const ev = evLine.replace("event:", "").trim();
        const data = dataLine.replace("data:", "").trim();
        if (ev === "insight_chunk") {
          try { log.append(JSON.parse(data).text); } catch {}
        } else {
          const span = document.createElement("span");
          span.className = "ev";
          span.textContent = `\n[${ev}] ${data}\n`;
          log.appendChild(span);
        }
        log.scrollTop = log.scrollHeight;
      }
    }
  } catch (e) {
    log.append("\n[error] " + e.message);
  } finally {
    btn.disabled = false;
  }
}

// --- Metrics -----------------------------------------------------------------
let latencyChart, providerChart;
async function refreshMetrics() {
  let m;
  try { m = await (await fetch("/metrics")).json(); } catch { return; }
  const cost = m.llm_cost_usd || { total: 0 };
  const lat = m.latency_ms || {};
  $("#metric-cards").innerHTML = `
    ${metricCard("Requests", m.counters?.["requests.total"] || 0, "total analyzed")}
    ${metricCard("Avg latency", (lat.avg || 0) + " ms", `p95 ${lat.p95 || 0} ms`)}
    ${metricCard("LLM tokens", (m.llm_tokens?.total) || 0, "across providers")}
    ${metricCard("Est. cost", fmtUsd(cost.total), "token-based")}`;

  const cb = m.circuit_breaker || {};
  const cache = m.cache || {};
  const guard = m.guardrails || {};
  $("#cb-kv").innerHTML =
    Object.entries(cb).map(([k, v]) => `<span>${esc(k)} <b>${v.open ? "OPEN" : "closed"}</b> (${v.failures} fails)</span>`).join("") +
    `<span>cache size <b>${cache.size ?? 0}</b></span><span>cache ttl <b>${cache.ttl_seconds ?? 0}s</b></span>` +
    `<span>guardrail flags <b>${guard.flagged_inputs ?? 0}</b></span>`;

  drawLatency(lat);
  drawProviders(m.providers || {});
}

function metricCard(title, big, sub) {
  return `<div class="card"><h3>${title}</h3><div class="big">${big}</div><div class="sub">${sub}</div></div>`;
}

function drawLatency(lat) {
  const ctx = $("#chart-latency");
  const data = [lat.min || 0, lat.p50 || 0, lat.avg || 0, lat.p95 || 0, lat.max || 0];
  if (latencyChart) { latencyChart.data.datasets[0].data = data; latencyChart.update(); return; }
  latencyChart = new Chart(ctx, {
    type: "bar",
    data: { labels: ["min", "p50", "avg", "p95", "max"], datasets: [{ data, backgroundColor: "#6c8cff" }] },
    options: baseChartOpts(),
  });
}

function drawProviders(providers) {
  const labels = Object.keys(providers);
  const calls = labels.map((l) => providers[l].calls);
  const fails = labels.map((l) => providers[l].failures);
  const ctx = $("#chart-providers");
  if (providerChart) {
    providerChart.data.labels = labels;
    providerChart.data.datasets[0].data = calls;
    providerChart.data.datasets[1].data = fails;
    providerChart.update();
    return;
  }
  providerChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "calls", data: calls, backgroundColor: "#56d4c4" },
        { label: "failures", data: fails, backgroundColor: "#ff5c7a" },
      ],
    },
    options: baseChartOpts(true),
  });
}

// --- Result charts -----------------------------------------------------------
function chartForResult(task, result) {
  if (task === "forecast_revenue" && result.forecast?.length) {
    return () => lineChart("result-chart", result.forecast.map((p) => p.date), result.forecast.map((p) => p.predicted_revenue), "predicted revenue");
  }
  if (task === "trend_analysis" && result.moving_average?.length) {
    const s = result.moving_average;
    return () => lineChart("result-chart", s.map((p) => p.date), s.map((p) => p.moving_average), "moving average");
  }
  if (task === "sales_by_region" && result.regions?.length) {
    return () => barChart("result-chart", result.regions.map((r) => r.region), result.regions.map((r) => r.revenue), "revenue");
  }
  return null;
}

function lineChart(id, labels, data, label) {
  new Chart($("#" + id), {
    type: "line",
    data: { labels, datasets: [{ label, data, borderColor: "#56d4c4", backgroundColor: "rgba(86,212,196,0.15)", fill: true, tension: 0.3 }] },
    options: baseChartOpts(),
  });
}
function barChart(id, labels, data, label) {
  new Chart($("#" + id), {
    type: "bar",
    data: { labels, datasets: [{ label, data, backgroundColor: "#6c8cff" }] },
    options: baseChartOpts(),
  });
}

function baseChartOpts(legend = false) {
  return {
    responsive: true,
    plugins: { legend: { display: legend, labels: { color: "#8b97b4" } } },
    scales: {
      x: { ticks: { color: "#8b97b4", maxRotation: 0, autoSkip: true }, grid: { color: "#263150" } },
      y: { ticks: { color: "#8b97b4" }, grid: { color: "#263150" } },
    },
  };
}

// --- Wire up -----------------------------------------------------------------
$("#btn-analyze").onclick = runAnalyze;
$("#btn-consensus").onclick = runConsensus;
$("#btn-stream").onclick = runStream;
$("#q-analyze").addEventListener("keydown", (e) => e.key === "Enter" && runAnalyze());
$("#q-consensus").addEventListener("keydown", (e) => e.key === "Enter" && runConsensus());
$("#q-stream").addEventListener("keydown", (e) => e.key === "Enter" && runStream());

refreshHealth();
setInterval(() => { if ($("#panel-metrics").classList.contains("active")) refreshMetrics(); }, 4000);
setInterval(refreshHealth, 15000);
