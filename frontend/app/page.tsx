"use client";

import { useEffect, useState } from "react";
import ChatWindow from "@/components/ChatWindow";
import DocumentList from "@/components/DocumentList";
import UploadDropzone from "@/components/UploadDropzone";
import { ApiError, listDocuments, type DocumentSummary } from "@/lib/api";

type DocumentsState = {
  documents: DocumentSummary[];
  loading: boolean;
  error: string | null;
};

// Never rejects, so callers can apply the result without their own try/catch.
async function fetchDocuments(): Promise<DocumentsState> {
  try {
    return { documents: await listDocuments(), loading: false, error: null };
  } catch (err) {
    const error = err instanceof ApiError ? err.message : "Could not load documents.";
    return { documents: [], loading: false, error };
  }
}

export default function Home() {
  const [state, setState] = useState<DocumentsState>({ documents: [], loading: true, error: null });
  const { documents, loading, error } = state;

  useEffect(() => {
    let cancelled = false;
    fetchDocuments().then((next) => {
      if (!cancelled) setState(next);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  function refresh() {
    fetchDocuments().then(setState);
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6">
      <header className="mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">RAG Chatbot with Citations</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Upload PDFs and ask questions. Every answer cites the document and page it came from.
        </p>
      </header>

      <div className="grid flex-1 gap-6 md:grid-cols-[320px_1fr]">
        <aside className="space-y-6">
          <section>
            <h2 className="mb-2 text-sm font-medium text-neutral-700">Upload</h2>
            <UploadDropzone onUploaded={refresh} />
          </section>
          <section>
            <h2 className="mb-2 text-sm font-medium text-neutral-700">Documents</h2>
            <DocumentList documents={documents} loading={loading} error={error} />
          </section>
        </aside>

        <div className="min-h-[520px]">
          <ChatWindow hasDocuments={documents.length > 0} />
        </div>
      </div>
    </main>
  );
}
