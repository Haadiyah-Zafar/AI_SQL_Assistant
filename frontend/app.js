const $ = (id) => document.getElementById(id);

const apiBaseInput = $("api-base");
const healthStatus = $("health-status");
const uploadResult = $("upload-result");
const databaseResult = $("database-result");
const databaseSelect = $("database-select");
const agentResult = $("agent-result");
const approvalPanel = $("approval-panel");
const approvalReason = $("approval-reason");
const approvalSql = $("approval-sql");
const resultsTableWrap = $("results-table-wrap");
const resultsTable = $("results-table");

let pendingApprovalId = null;

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${apiBase()}${path}`, options);
  const text = await response.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  if (!response.ok) {
    const detail = body?.detail ?? body ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail, null, 2));
  }
  return body;
}

function showJson(el, data) {
  el.textContent = JSON.stringify(data, null, 2);
}

function setHealth(ok, message) {
  healthStatus.textContent = message;
  healthStatus.className = `status ${ok ? "ok" : "error"}`;
}

async function checkHealth() {
  try {
    const data = await apiFetch("/health");
    setHealth(true, `Backend OK (${data.status})`);
  } catch (error) {
    setHealth(false, `Backend unreachable: ${error.message}`);
  }
}

async function refreshDatabases() {
  const databases = await apiFetch("/api/databases");
  databaseSelect.innerHTML = '<option value="">Select a database…</option>';
  for (const db of databases) {
    const option = document.createElement("option");
    option.value = db.database_id;
    option.textContent = `${db.original_filename} (${db.table_count} tables)`;
    databaseSelect.appendChild(option);
  }
  showJson(databaseResult, databases);
}

async function uploadDatabase() {
  const fileInput = $("upload-file");
  if (!fileInput.files.length) {
    throw new Error("Choose a file first.");
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const data = await apiFetch("/api/upload", {
    method: "POST",
    body: formData,
  });

  showJson(uploadResult, data);
  await refreshDatabases();
  databaseSelect.value = data.database.database_id;
}

async function indexRag() {
  const databaseId = databaseSelect.value;
  if (!databaseId) {
    throw new Error("Select a database first.");
  }
  const data = await apiFetch(`/api/rag/databases/${databaseId}/index`, {
    method: "POST",
  });
  showJson(databaseResult, data);
}

function renderQueryTable(queryResult) {
  if (!queryResult?.columns?.length) {
    resultsTableWrap.classList.add("hidden");
    return;
  }

  resultsTable.innerHTML = "";
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const column of queryResult.columns) {
    const th = document.createElement("th");
    th.textContent = column;
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);
  resultsTable.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const row of queryResult.rows) {
    const tr = document.createElement("tr");
    for (const column of queryResult.columns) {
      const td = document.createElement("td");
      const value = row[column];
      td.textContent = value === null || value === undefined ? "" : String(value);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  resultsTable.appendChild(tbody);
  resultsTableWrap.classList.remove("hidden");
}

function showApproval(response) {
  if (!response.approval_id) {
    approvalPanel.classList.add("hidden");
    pendingApprovalId = null;
    return;
  }

  pendingApprovalId = response.approval_id;
  approvalReason.textContent = `Approval ${response.approval_status ?? "pending"} — id: ${response.approval_id}`;
  approvalSql.textContent = response.generated_sql ?? "";
  approvalPanel.classList.remove("hidden");
}

async function askAgent() {
  const databaseId = databaseSelect.value;
  const question = $("question-input").value.trim();

  if (!databaseId) {
    throw new Error("Select a database first.");
  }
  if (!question) {
    throw new Error("Enter a question.");
  }

  const response = await apiFetch("/api/agent/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ database_id: databaseId, question }),
  });

  showJson(agentResult, response);
  showApproval(response);
  renderQueryTable(response.query_result);
}

async function decideApproval(approved) {
  if (!pendingApprovalId) {
    throw new Error("No pending approval.");
  }

  const response = await apiFetch(`/api/approvals/${pendingApprovalId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });

  showJson(agentResult, response);
  approvalPanel.classList.add("hidden");
  pendingApprovalId = null;
}

async function runAction(action) {
  try {
    await action();
  } catch (error) {
    alert(error.message);
  }
}

$("refresh-health").addEventListener("click", () => runAction(checkHealth));
$("upload-btn").addEventListener("click", () => runAction(uploadDatabase));
$("refresh-databases").addEventListener("click", () => runAction(refreshDatabases));
$("index-rag-btn").addEventListener("click", () => runAction(indexRag));
$("ask-btn").addEventListener("click", () => runAction(askAgent));
$("approve-btn").addEventListener("click", () => runAction(() => decideApproval(true)));
$("reject-btn").addEventListener("click", () => runAction(() => decideApproval(false)));

checkHealth();
refreshDatabases().catch(() => {});
