import CitationList from "@/components/CitationList";
import type { Citation } from "@/lib/api";

export type Message =
  | { id: number; role: "user"; content: string }
  | { id: number; role: "assistant"; content: string; citations: Citation[]; refused: boolean }
  | { id: number; role: "error"; content: string };

type Props = {
  message: Message;
};

export default function MessageBubble({ message }: Props) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-lg bg-neutral-900 px-3.5 py-2 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.role === "error") {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] rounded-lg border border-red-200 bg-red-50 px-3.5 py-2 text-sm text-red-800" role="alert">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.refused) {
    return (
      <div className="flex justify-start">
        <div
          className="max-w-[80%] rounded-lg border border-neutral-200 bg-neutral-100 px-3.5 py-2 text-sm text-neutral-500"
          data-testid="refusal"
        >
          <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-neutral-400">
            Not in documents
          </span>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] rounded-lg border border-neutral-200 bg-white px-3.5 py-2 text-sm text-neutral-800" data-testid="answer">
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        {message.citations.length > 0 && <CitationList citations={message.citations} />}
      </div>
    </div>
  );
}
