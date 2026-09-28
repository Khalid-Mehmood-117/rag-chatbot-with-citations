import type { DocumentSummary } from "@/lib/api";

type Props = {
  documents: DocumentSummary[];
  loading: boolean;
  error: string | null;
};

function formatUploadedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function DocumentList({ documents, loading, error }: Props) {
  if (loading) {
    return <p className="text-sm text-neutral-500">Loading documents...</p>;
  }
  if (error) {
    return (
      <p className="text-sm text-red-700" role="alert">
        {error}
      </p>
    );
  }
  if (documents.length === 0) {
    return <p className="text-sm text-neutral-500">No documents yet. Upload a PDF to get started.</p>;
  }
  return (
    <ul className="divide-y divide-neutral-200 rounded-md border border-neutral-200" data-testid="document-list">
      {documents.map((doc) => (
        <li key={doc.id} className="px-3 py-2 text-sm">
          <p className="truncate font-medium text-neutral-800" title={doc.name}>
            {doc.name}
          </p>
          <p className="text-neutral-500">
            {doc.pages} {doc.pages === 1 ? "page" : "pages"} · uploaded {formatUploadedAt(doc.uploaded_at)}
          </p>
        </li>
      ))}
    </ul>
  );
}
