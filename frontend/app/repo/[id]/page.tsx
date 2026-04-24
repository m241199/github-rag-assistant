"use client";

import { useState } from "react";
import ChatBox from "../../../components/ChatBox";
import AnswerPanel from "../../../components/AnswerPanel";
import SourceList from "../../../components/SourceList";

export default function RepoPage() {
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<
    { file_path: string; section_title?: string | null; symbol_name?: string | null; snippet: string }[]
  >([]);

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <h1 className="text-3xl font-bold">Repository Assistant</h1>
        <ChatBox setAnswer={setAnswer} setSources={setSources} />
        <AnswerPanel answer={answer} />
        <SourceList sources={sources} />
      </div>
    </main>
  );
}