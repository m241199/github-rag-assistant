"use client";

import { useState } from "react";
import { askQuestion } from "../lib/api";

type Source = {
  file_path: string;
  section_title?: string | null;
  symbol_name?: string | null;
  snippet: string;
};

type Props = {
  setAnswer: (answer: string) => void;
  setSources: (sources: Source[]) => void;
};

export default function ChatBox({ setAnswer, setSources }: Props) {
  const [question, setQuestion] = useState("");
  const [repoId, setRepoId] = useState("");

  const handleAsk = async () => {
    try {
      const data = await askQuestion(repoId, question);
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (error) {
      setAnswer("Failed to get answer.");
      setSources([]);
    }
  };

  return (
    <div className="space-y-3 rounded-xl border p-4">
      <input
        type="text"
        placeholder="Repo ID"
        value={repoId}
        onChange={(e) => setRepoId(e.target.value)}
        className="w-full rounded-md border px-3 py-2"
      />
      <textarea
        placeholder="Ask a question about the repo..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        className="min-h-[120px] w-full rounded-md border px-3 py-2"
      />
      <button
        onClick={handleAsk}
        className="rounded-md bg-blue-600 px-4 py-2 text-white"
      >
        Ask
      </button>
    </div>
  );
}
