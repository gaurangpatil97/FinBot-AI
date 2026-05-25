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
  if (!res.ok) throw new Error("Failed to create company");
  return res.json();
}

export async function getCompanyStatus(slug: string) {
  const res = await fetch(`${BASE_URL}/api/v1/companies/${slug}/status`);
  if (!res.ok) throw new Error("Failed to fetch company status");
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
  year?: string
) {
  const res = await fetch(`${BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, company_slug: companySlug, year }),
  });
  if (!res.ok) throw new Error("Failed to query");
  return res.json();
}
