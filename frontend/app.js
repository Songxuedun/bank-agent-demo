"use strict";
// ===== 基础工具 =====
const $ = (id) => document.getElementById(id);
const money = (n) => (n == null ? "-" : "¥" + Number(n).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
let token = localStorage.getItem("token") || "";
let authMode = "login";
let billChart = null;

// 用 DOM API 构造节点，所有文本走 textContent，避免把模型/服务端返回内容当 HTML 执行
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  kids.flat().forEach((c) => n.append(c instanceof Node ? c : document.createTextNode(String(c))));
  return n;
}

function toast(text) {
  const t = $("toast");
  t.textContent = text;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

async function api(path, { method = "GET", body } = {}) {
  const res = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: "Bearer " + token } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (_) { /* 非 JSON 响应 */ }
  if (res.status === 401 && token) { logout(); throw new Error("登录已过期，请重新登录"); }
  if (!res.ok) throw new Error(data.detail || "请求失败(" + res.status + ")");
  return data;
}

// ===== 注册 / 登录 =====
function switchAuth(mode) {
  authMode = mode;
  $("tab-login").classList.toggle("active", mode === "login");
  $("tab-register").classList.toggle("active", mode === "register");
  document.querySelectorAll(".reg-only").forEach((n) => n.classList.toggle("hidden", mode === "login"));
  $("auth-submit").textContent = mode === "login" ? "登录" : "注册并登录";
  $("f-pass").autocomplete = mode === "login" ? "current-password" : "new-password";
  $("auth-error").textContent = "";
}

async function submitAuth(e) {
  e.preventDefault();
  const btn = $("auth-submit");
  btn.disabled = true;
  $("auth-error").textContent = "";
  try {
    const body = { username: $("f-user").value.trim(), password: $("f-pass").value };
    if (authMode === "register") {
      body.name = $("f-name").value.trim();
      body.phone = $("f-phone").value.trim();
    }
    const data = await api(authMode === "login" ? "/login" : "/register", { method: "POST", body });
    token = data.token;
    localStorage.setItem("token", token);
    $("f-pass").value = "";
    await enterApp(data.user);
  } catch (err) {
    $("auth-error").textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

function logout() {
  token = "";
  localStorage.removeItem("token");
  $("app").classList.add("hidden");
  $("auth").classList.remove("hidden");
  $("chat-log").replaceChildren();
}

async function enterApp(user) {
  $("auth").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("user-name").textContent = user.name;
  addMsg("sys", "你好 " + user.name + "，我可以帮你查账单、转账、买理财。试试说“给妈妈转 200 元”。");
  go("dashboard");
}

// ===== 页面切换与数据加载 =====
const loaders = { dashboard: loadDashboard, transfer: loadTransfer, bill: loadBill, wealth: loadWealth, audit: loadAudit };

function go(page) {
  if (!loaders[page]) return;
  document.querySelectorAll(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + page));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  const sec = $("page-" + page);
  sec.classList.remove("flash");
  void sec.offsetWidth;
  sec.classList.add("flash");
  return loaders[page]().catch((e) => toast(e.message));
}

async function refreshAll() {
  const active = document.querySelector(".page.active");
  if (active) await loaders[active.id.replace("page-", "")]().catch(() => {});
}

async function loadDashboard() {
  const s = (await api("/query/get_summary")).data;
  $("d-balance").textContent = money(s.balance);
  $("d-expense").textContent = money(s.month_expense);
  $("d-income").textContent = money(s.month_income);
  $("d-rate").textContent = s.savings_rate == null ? "-" : s.savings_rate + "%";
  $("d-portfolio").textContent = "总现值 " + money(s.portfolio_value);
  const prods = (await api("/query/get_products")).data.products.slice(0, 3);
  renderProducts($("d-recs"), prods);
}

async function loadTransfer() {
  const list = (await api("/query/get_contacts")).data.contacts;
  $("t-contacts").replaceChildren(...list.map((c) =>
    el("button", { class: "chip", type: "button", onclick: () => { $("t-to").value = c.name; } }, c.name)));
}

function updateRiskHint() {
  const amt = Number($("t-amount").value);
  const h = $("t-risk");
  if (amt > 1000) h.textContent = "该金额属于红色操作，提交后需要输入验证码";
  else if (amt > 0) h.textContent = "该金额属于黄色操作，提交后需要您确认";
  else h.textContent = "单笔不超过 1000 元需确认；超过需验证码";
}

async function loadBill() {
  const d = (await api("/query/get_statement")).data;
  $("b-expense").textContent = money(d.total_spending);
  $("b-income").textContent = money(d.total_income);
  $("b-rate").textContent = d.savings_rate == null ? "-" : d.savings_rate + "%";
  $("b-top").textContent = d.top_category || "-";
  $("b-insights").replaceChildren(...(d.insights || []).map((t) => el("li", {}, t)));
  const labels = Object.keys(d.by_category || {});
  if (billChart) billChart.destroy();
  if (typeof Chart === "undefined") return toast("图表库加载失败，请检查网络");
  billChart = new Chart($("bill-chart"), {
    type: "doughnut",
    data: { labels, datasets: [{ data: labels.map((k) => d.by_category[k]),
      backgroundColor: ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7", "#94a3b8"], borderColor: "#1e293b" }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { color: "#f1f5f9" } } } },
  });
}

function renderProducts(box, prods) {
  box.replaceChildren(...prods.map((p) => el("div", { class: "rec" },
    el("b", {}, p.name), el("span", { class: "muted small" }, p.tag + " · 起投 ¥" + p.min_amount),
    el("div", { class: "rate" }, p.annual_rate), el("p", {}, p.description),
    el("button", { class: "btn primary", onclick: () => buyFlow(p) }, "申购"))));
}

async function loadWealth() {
  const [h, analysis] = await Promise.all([
    (await api("/query/get_portfolio")).data,
    (await api("/query/get_wealth_analysis?risk_code=" + ($("w-risk")?.value || "balanced"))).data,
  ]);
  $("w-total").textContent = "总现值 " + money(h.total_value);
  $("w-holdings").replaceChildren(...h.holdings.map((x) => el("tr", {},
    el("td", {}, x.name), el("td", {}, money(x.amount)), el("td", {}, money(x.current_value)),
    el("td", { class: x.profit_loss >= 0 ? "pos" : "neg" }, money(x.profit_loss)),
    el("td", {}, el("button", { class: "btn ghost", onclick: () => submitAction("redeem_product", { product_name: x.name }) }, "赎回")))));
  renderWealthAnalysis(analysis);
  renderWealthProducts(analysis.products);
}

function renderWealthAnalysis(a) {
  const box = $("w-analysis");
  if (!box) return;
  const inv = a.investor, budget = a.risk_budget, cs = a.core_satellite;
  const compl = a.compliance;
  const parts = [
    el("div", { class: "w-kv" },
      el("span", {}, "投资者等级"),
      el("b", {}, `${inv.code} ${inv.name}（只能买风险等级 ≤ ${inv.risk_level} 的产品）`)),
    el("div", { class: "w-kv" },
      el("span", {}, "可投资金额"),
      el("b", {}, money(a.investable_amount))),
    el("div", { class: "w-kv" },
      el("span", {}, "风险预算"),
      el("b", {}, budget.note)),
    el("div", { class: "w-kv" },
      el("span", {}, "合规匹配"),
      el("b", {},
        el("span", { class: "w-badge ok" }, "可买：" + (compl.allowed.join("、") || "无")),
        el("span", { class: "w-badge warn" }, compl.blocked.length ? "超出等级：" + compl.blocked.join("、") : ""))),
    el("div", { class: "w-kv" },
      el("span", {}, "核心–卫星"),
      el("b", {}, `核心 ${cs.core_pct}%（${cs.core.join("、")}）＋ 卫星 ${cs.satellite_pct}%（${cs.satellite.join("、") || "暂不配置"}）`)),
    el("div", { class: "w-steps" }, ...a.five_step.map((s) =>
      el("div", { class: "w-step" }, el("b", {}, s.step), el("span", {}, s.content)))),
    el("div", { class: "w-disc" }, a.disclaimer),
  ];
  box.replaceChildren(...parts);
}

function renderWealthProducts(prods) {
  const box = $("w-products");
  if (!box) return;
  box.replaceChildren(...prods.map((p) => el("div", { class: "rec" },
    el("b", {}, p.name),
    el("span", { class: "muted small" }, p.category + " · " + p.risk_name),
    el("div", { class: "rate" }, p.annual_rate),
    el("div", { class: "w-attr" },
      el("span", {}, "业绩基准 " + p.benchmark),
      el("span", {}, "费后 " + p.fee_after_rate + "%"),
      el("span", {}, "夏普 " + p.sharpe),
      el("span", {}, "回撤 " + p.max_drawdown + "%"),
      el("span", {}, "期限 " + p.term),
      el("span", {}, "底层 " + p.underlying)),
    el("p", {}, p.description),
    el("div", { class: "w-attr" },
      el("span", { class: p.fit === "合规可买" ? "w-badge ok" : "w-badge warn" }, p.fit),
      el("span", { class: "muted small" }, "安全 " + p.safety_score.score + "/5 · 收益 " + p.return_score.score + "/5")),
    el("button", { class: "btn primary", onclick: () => buyFlow({ name: p.name, min_amount: p.min_amount }) }, "申购"))));
}

async function loadAudit() {
  const logs = (await api("/audit")).logs;
  $("a-rows").replaceChildren(...logs.map((l) => el("tr", {},
    el("td", {}, l.time), el("td", {}, l.operation), el("td", {}, l.tool || "-"),
    el("td", {}, l.risk || "-"), el("td", {}, l.mfa || "-"), el("td", {}, l.result || "-"))));
}

function buyFlow(p) {
  const v = window.prompt("申购 " + p.name + "，请输入金额(元)，起投 ¥" + p.min_amount, String(p.min_amount));
  const amount = Number(v);
  if (v === null) return;
  if (!(amount > 0)) return toast("请输入有效金额");
  submitAction("buy_product", { product_name: p.name, amount });
}

// ===== 确认 / 验证码弹窗 (界面表单和 AI 对话共用) =====
let pending = null;

function openPending(p) {
  pending = p;
  const red = p.type === "mfa";
  $("m-title").textContent = red ? "需要身份验证 (红色操作)" : "请确认操作 (黄色操作)";
  $("m-body").textContent = p.content;
  $("m-mfa").classList.toggle("hidden", !red);
  $("m-code").value = "";
  $("m-error").textContent = "";
  $("modal").querySelector(".modal-box").className = "modal-box " + (red ? "red" : "yellow");
  $("modal").classList.remove("hidden");
  (red ? $("m-code") : $("m-ok")).focus();
}

function closeModal() {
  $("modal").classList.add("hidden");
  pending = null;
}

async function confirmPending() {
  if (!pending) return;
  const btn = $("m-ok");
  btn.disabled = true;
  try {
    const r = await api("/confirm", { method: "POST", body: { pending_id: pending.pending_id, mfa_code: $("m-code").value.trim() } });
    if (r.need_mfa) { $("m-error").textContent = r.error; return; }
    if (!r.success) { $("m-error").textContent = r.error || "执行失败"; if (!/验证/.test(r.error || "")) closeModal(); return; }
    closeModal();
    toast(r.message || "操作成功");
    addMsg("sys", "已执行: " + (r.message || "操作成功"));
    await refreshAll();
  } catch (e) {
    $("m-error").textContent = e.message;
  } finally {
    btn.disabled = false;
  }
}

async function cancelPending() {
  if (pending) await api("/cancel", { method: "POST", body: { pending_id: pending.pending_id } }).catch(() => {});
  closeModal();
  addMsg("sys", "已取消操作");
}

// 界面手动发起的操作也走服务端的同一套权限判定
async function submitAction(tool, params) {
  try {
    const r = await api("/action", { method: "POST", body: { tool, params } });
    if (r.pending_id) return openPending(r);
    if (r.success) { toast(r.message || "操作成功"); await refreshAll(); }
    else toast(r.error || "操作失败");
  } catch (e) { toast(e.message); }
}

// ===== AI 对话 =====
function addMsg(kind, text) {
  const m = el("div", { class: "msg " + kind }, text);
  $("chat-log").append(m);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
  return m;
}

// 执行模型返回的界面动作: 只认白名单页面，其余忽略
async function applyUi(actions, pend) {
  for (const a of actions || []) {
    if (a.type === "navigate") await go(a.page);
  }
  if (pend && pend.tool_name === "transfer") {
    await go("transfer");
    $("t-to").value = pend.params.to || "";
    $("t-amount").value = pend.params.amount ?? "";
    $("t-memo").value = pend.params.memo || "";
    updateRiskHint();
  }
}

async function sendChat(text) {
  addMsg("user", text);
  const wait = addMsg("sys", "AI 正在处理…");
  $("chat-input").disabled = true;
  try {
    const r = await api("/chat", { method: "POST", body: { message: text } });
    wait.remove();
    addMsg("bot", r.content || "(无回复)");
    const pend = r.pending_id ? r : null;
    await applyUi(r.ui_actions, pend);
    if (pend) openPending(pend);
    else if ((r.tool_runs || []).some((t) => !["get_balance"].includes(t.tool) && t.success)) await refreshAll();
  } catch (e) {
    wait.remove();
    addMsg("sys", "出错: " + e.message);
  } finally {
    $("chat-input").disabled = false;
    $("chat-input").focus();
  }
}

// ===== 初始化 =====
document.addEventListener("DOMContentLoaded", async () => {
  switchAuth("login");
  document.querySelectorAll(".nav-btn").forEach((b) => b.addEventListener("click", () => go(b.dataset.page)));
  document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));
  $("t-amount").addEventListener("input", updateRiskHint);
  $("t-submit").addEventListener("click", () => {
    const to = $("t-to").value.trim();
    const amount = Number($("t-amount").value);
    if (!to || !(amount > 0)) return toast("请填写收款人和有效金额");
    submitAction("transfer", { to, amount, memo: $("t-memo").value.trim() });
  });
  $("m-ok").addEventListener("click", confirmPending);
  $("m-cancel").addEventListener("click", cancelPending);
  $("m-code").addEventListener("keydown", (e) => { if (e.key === "Enter") confirmPending(); });
  $("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const v = $("chat-input").value.trim();
    if (!v) return;
    $("chat-input").value = "";
    sendChat(v);
  });
  document.querySelectorAll("#chat-quick button").forEach((b) => b.addEventListener("click", () => sendChat(b.textContent)));
  const wRisk = $("w-risk");
  if (wRisk) wRisk.addEventListener("change", () => { wRisk.disabled = true; loadWealth().finally(() => { wRisk.disabled = false; }); });

  if (token) {
    try { await enterApp(await api("/me")); } catch (_) { /* api() 已在 401 时登出 */ }
  }
});
