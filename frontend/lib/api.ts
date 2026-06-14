const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getCompanies() {
  const res = await fetch(`${BASE_URL}/api/v1/companies`);
  if (!res.ok) throw new Error("Failed to fetch companies");
  return res.json();
}

export async function createCompany(name: string, slug: string, ticker: string) {
  const res = await fetch(`${BASE_URL}/api/v1/companies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, slug, ticker }),
  });

  if (res.status === 409) {
    return res.json();
  }

  if (!res.ok) throw new Error("Failed to create company");
  return res.json();
}

export async function getCompanyStatus(slug: string) {
  const res = await fetch(`${BASE_URL}/api/v1/companies/${slug}/status`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function getCompanyKpi(slug: string, metric: string, year: string) {
  const params = new URLSearchParams({ metric, year });
  const res = await fetch(`${BASE_URL}/api/v1/companies/${slug}/kpis?${params.toString()}`);

  if (!res.ok) {
    throw new Error("Failed to fetch KPI");
  }

  return res.json();
}

export async function getCompanyFiles(slug: string) {
  const res = await fetch(`${BASE_URL}/api/v1/companies/${slug}/files`);
  if (!res.ok) throw new Error("Failed to fetch company files");
  return res.json();
}

export async function uploadFile(
  file: File,
  companySlug: string,
  fileType: string,
  year?: string,
  quarter?: string
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company_slug", companySlug);
  formData.append("file_type", fileType);
  if (year) formData.append("year", year);
  if (quarter) formData.append("quarter", quarter);

  const res = await fetch(`${BASE_URL}/api/v1/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload file");
  return res.json();
}

export async function generateEmbeddings(companySlug: string) {
  const res = await fetch(`${BASE_URL}/api/v1/embed/${companySlug}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to start embedding");
  return res.json();
}

export async function queryRAG(
  question: string,
  companySlug: string,
  year?: string,
  sessionId?: string
) {
  const body: any = { question, company_slug: companySlug };
  if (year) body.year = year;
  if (sessionId) body.session_id = sessionId;
  
  const res = await fetch(`${BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to query");
  return res.json();
}

export async function createSession(companySlug: string, title: string) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company_slug: companySlug, title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSessions(companySlug: string) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions?company_slug=${encodeURIComponent(companySlug)}`);
  if (!res.ok) throw new Error("Failed to get sessions");
  return res.json();
}

export async function getSessionMessages(sessionId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`);
  if (!res.ok) throw new Error("Failed to get session messages");
  return res.json();
}

export async function renameSession(sessionId: string, title: string) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename session");
  return res.json();
}

export async function deleteSession(sessionId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete session");
  return res.json();
}

export async function generateChart(companySlug: string, metrics: string[], years?: string[], chartTypeHint?: string) {
  const body: any = { company_slug: companySlug, metrics };
  if (years) body.years = years;
  if (chartTypeHint) body.chart_type_hint = chartTypeHint;

  const res = await fetch(`${BASE_URL}/api/v1/chart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to generate chart");
  return res.json();
}

export async function analyzeData(companySlug: string, metrics: string[], years?: string[], chartTypeHint?: string, question?: string) {
  const body: any = { company_slug: companySlug, metrics };
  if (years) body.years = years;
  if (chartTypeHint) body.chart_type_hint = chartTypeHint;
  if (question) body.question = question;

  const res = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to analyze data");
  return res.json();
}

export async function saveMessage(
  sessionId: string,
  role: string,
  content: string,
  citations: any[] = [],
  routingDebug: any = {},
  latency: number = 0,
  chunks: any[] = [],
  chartData: any = null
) {
  const res = await fetch(`${BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      content,
      citations,
      routing_debug: routingDebug,
      latency,
      chunks,
      chart_data: chartData,
    }),
  });
  if (!res.ok) throw new Error("Failed to save message");
  return res.json();
}
