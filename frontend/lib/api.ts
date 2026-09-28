// Typed client for the FastAPI backend. Every function throws ApiError on failure,
// so callers handle one error type.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DocumentSummary = {
  id: string;
  name: string;
  pages: number;
  chunks: number;
  uploaded_at: string;
};

export type UploadResult = {
  id: string;
  name: string;
  pages: number;
  chunks: number;
};

export type Citation = {
  index: number;
  document: string;
  page: number;
  snippet: string;
};

export type AskResponse = {
  answer: string;
  citations: Citation[];
  refused: boolean;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return `Request failed with status ${status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(`Could not reach the backend at ${API_URL}`, 0);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(errorMessage(body, response.status), response.status);
  }
  return body as T;
}

export function listDocuments(): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>("/documents");
}

export function askQuestion(question: string): Promise<AskResponse> {
  return request<AskResponse>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

// Uses XMLHttpRequest because fetch does not report upload progress.
export function uploadDocument(
  file: File,
  onProgress: (percent: number) => void,
): Promise<UploadResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append("file", file);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        body = null;
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as UploadResult);
      } else {
        reject(new ApiError(errorMessage(body, xhr.status), xhr.status));
      }
    };

    xhr.onerror = () => reject(new ApiError(`Could not reach the backend at ${API_URL}`, 0));
    xhr.open("POST", `${API_URL}/documents`);
    xhr.send(form);
  });
}
