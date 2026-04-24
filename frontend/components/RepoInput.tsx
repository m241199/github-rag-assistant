"use client";

import { useState } from "react";
import { createRepo, indexRepo } from "../lib/api";

export default function RepoInput() {
  const [repoUrl, setRepoUrl] = useState("");
  const [result, setResult] = useState<string>("");

  const handleSubmit = async () => {
    try {
      setResult("Creating repository record...");
      const data = await createRepo(repoUrl);
      setResult(`Indexing ${data.name}...`);

      const indexed = await indexRepo(data.id);
      setResult(`Indexed ${indexed.files} files into ${indexed.chunks} chunks. Repo ID: ${data.id}`);
    } catch (error) {
      setResult("Failed to create or index repo.");
    }
  };

  return (
    <div className="space-y-3 rounded-xl border p-4">
      <input
        type="text"
        placeholder="https://github.com/owner/repo"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        className="w-full rounded-md border px-3 py-2"
      />
      <button
        onClick={handleSubmit}
        className="rounded-md bg-black px-4 py-2 text-white"
      >
        Create Repo
      </button>
      {result && <p className="text-sm text-gray-700">{result}</p>}
    </div>
  );
}
