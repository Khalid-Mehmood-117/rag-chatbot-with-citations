"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import MessageBubble, { type Message } from "@/components/MessageBubble";
import { ApiError, askQuestion } from "@/lib/api";

type Props = {
  hasDocuments: boolean;
};

// Omit applied to each member of the union, so every message shape keeps its own fields.
type NewMessage = Message extends infer M ? (M extends Message ? Omit<M, "id"> : never) : never;

export default function ChatWindow({ hasDocuments }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const nextId = useRef(1);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages, pending]);

  function push(message: NewMessage) {
    setMessages((current) => [...current, { ...message, id: nextId.current++ } as Message]);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    push({ role: "user", content: trimmed });
    setQuestion("");
    setPending(true);
    try {
      const response = await askQuestion(trimmed);
      push({
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        refused: response.refused,
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Something went wrong.";
      push({ role: "error", content: message });
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex h-full flex-col rounded-md border border-neutral-200 bg-white">
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4" data-testid="messages">
        {messages.length === 0 && !pending && (
          <p className="text-sm text-neutral-500">
            {hasDocuments
              ? "Ask a question about the uploaded documents. Answers cite the document and page they came from."
              : "Upload a PDF first, then ask questions about it here."}
          </p>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {pending && (
          <div className="flex justify-start" aria-live="polite">
            <div className="rounded-lg border border-neutral-200 bg-white px-3.5 py-2 text-sm text-neutral-500">
              Searching the documents...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={onSubmit} className="flex gap-2 border-t border-neutral-200 p-3">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your documents"
          aria-label="Question"
          disabled={pending}
          maxLength={2000}
          className="flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-blue-600 disabled:bg-neutral-50"
        />
        <button
          type="submit"
          disabled={pending || question.trim().length === 0}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
        >
          Ask
        </button>
      </form>
    </section>
  );
}
