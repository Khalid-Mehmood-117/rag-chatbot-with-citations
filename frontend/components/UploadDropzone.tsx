"use client";

import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { ApiError, uploadDocument, type UploadResult } from "@/lib/api";

type Status =
  | { kind: "idle" }
  | { kind: "uploading"; percent: number; name: string }
  | { kind: "processing"; name: string }
  | { kind: "done"; result: UploadResult }
  | { kind: "error"; message: string };

type Props = {
  onUploaded: (result: UploadResult) => void;
};

export default function UploadDropzone({ onUploaded }: Props) {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const busy = status.kind === "uploading" || status.kind === "processing";

  async function upload(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatus({ kind: "error", message: "Only PDF files are accepted." });
      return;
    }
    setStatus({ kind: "uploading", percent: 0, name: file.name });
    try {
      const result = await uploadDocument(file, (percent) => {
        // The backend embeds the file after the bytes arrive, so 100% means "processing".
        if (percent >= 100) {
          setStatus({ kind: "processing", name: file.name });
        } else {
          setStatus({ kind: "uploading", percent, name: file.name });
        }
      });
      setStatus({ kind: "done", result });
      onUploaded(result);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Upload failed.";
      setStatus({ kind: "error", message });
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    if (busy) return;
    const file = event.dataTransfer.files[0];
    if (file) void upload(file);
  }

  function onDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!busy) setDragging(true);
  }

  function onChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) void upload(file);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a PDF"
        aria-busy={busy}
        onClick={() => !busy && inputRef.current?.click()}
        onKeyDown={(event) => {
          if ((event.key === "Enter" || event.key === " ") && !busy) inputRef.current?.click();
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={() => setDragging(false)}
        className={`rounded-md border border-dashed px-4 py-8 text-center text-sm transition-colors ${
          dragging ? "border-blue-500 bg-blue-50" : "border-neutral-300 bg-neutral-50"
        } ${busy ? "cursor-wait" : "cursor-pointer hover:border-neutral-400"}`}
      >
        <p className="font-medium text-neutral-800">Drop a PDF here or click to choose</p>
        <p className="mt-1 text-neutral-500">Up to 25 MB, text-based PDFs only</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={onChange}
          data-testid="file-input"
        />
      </div>

      <div className="mt-3 min-h-6 text-sm" aria-live="polite">
        {status.kind === "uploading" && (
          <div>
            <div className="flex justify-between text-neutral-600">
              <span className="truncate">Uploading {status.name}</span>
              <span>{status.percent}%</span>
            </div>
            <div className="mt-1 h-1.5 w-full rounded bg-neutral-200">
              <div className="h-1.5 rounded bg-blue-600" style={{ width: `${status.percent}%` }} />
            </div>
          </div>
        )}
        {status.kind === "processing" && (
          <p className="text-neutral-600">Extracting text and building embeddings for {status.name}...</p>
        )}
        {status.kind === "done" && (
          <p className="text-green-700" data-testid="upload-result">
            Indexed <span className="font-medium">{status.result.name}</span>: {status.result.pages} pages,{" "}
            {status.result.chunks} chunks
          </p>
        )}
        {status.kind === "error" && (
          <p className="text-red-700" role="alert">
            {status.message}
          </p>
        )}
      </div>
    </div>
  );
}
