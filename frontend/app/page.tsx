"use client";

import { FormEvent, useState } from "react";
import { askQuestion, createRepo, indexRepo } from "../lib/api";

type Source = {
  file_path: string;
  section_title?: string | null;
  symbol_name?: string | null;
  snippet: string;
};

type RepoState = {
  id: string;
  name: string;
  github_url: string;
  files?: number;
  chunks?: number;
};

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/m241199/WASA.git");
  const [question, setQuestion] = useState("What does this project do?");
  const [repo, setRepo] = useState<RepoState | null>(null);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [status, setStatus] = useState("Paste a GitHub repository URL to begin.");
  const [isIndexing, setIsIndexing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

  async function handleIndex(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAnswer("");
    setSources([]);
    setIsIndexing(true);

    try {
      setStatus("Creating repository record...");
      const created = await createRepo(repoUrl.trim());
      setRepo({
        id: created.id,
        name: created.name,
        github_url: created.github_url,
      });

      setStatus(`Indexing ${created.name}. This can take a little while for larger repos...`);
      const indexed = await indexRepo(created.id);
      setRepo({
        id: created.id,
        name: created.name,
        github_url: created.github_url,
        files: indexed.files,
        chunks: indexed.chunks,
      });
      setStatus(`Indexed ${indexed.files} files into ${indexed.chunks} chunks.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to index repository.");
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!repo) {
      setStatus("Index a repository before asking a question.");
      return;
    }

    setIsAsking(true);
    setAnswer("");
    setSources([]);

    try {
      setStatus("Searching indexed context and asking the model...");
      const result = await askQuestion(repo.id, question.trim());
      setAnswer(result.answer);
      setSources(result.sources || []);
      setStatus(`Answered using ${result.sources?.length || 0} source chunks.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to answer question.");
    } finally {
      setIsAsking(false);
    }
  }

  const canAsk = Boolean(repo) && !isIndexing && !isAsking;

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>GitHub RAG Assistant</h1>
            <p>Index a public GitHub repository, ask a question, and inspect the sources used for the answer.</p>
          </div>
          <div className="status-pill">{repo ? repo.name : "No repo indexed"}</div>
        </header>

        <div className="grid">
          <section className="panel controls">
            <form onSubmit={handleIndex} className="stack">
              <label htmlFor="repo-url">GitHub repository</label>
              <input
                id="repo-url"
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/owner/repo"
                disabled={isIndexing}
              />
              <button type="submit" disabled={isIndexing || !repoUrl.trim()}>
                {isIndexing ? "Indexing..." : "Create and index"}
              </button>
            </form>

            {repo && (
              <div className="repo-summary">
                <div>
                  <span>Repository</span>
                  <strong>{repo.name}</strong>
                </div>
                <div>
                  <span>Repo ID</span>
                  <code>{repo.id}</code>
                </div>
                {typeof repo.files === "number" && (
                  <div className="metrics">
                    <strong>{repo.files} files</strong>
                    <strong>{repo.chunks} chunks</strong>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleAsk} className="stack">
              <label htmlFor="question">Question</label>
              <textarea
                id="question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask something about the indexed repository..."
                disabled={!canAsk}
              />
              <button type="submit" disabled={!canAsk || !question.trim()}>
                {isAsking ? "Asking..." : "Ask question"}
              </button>
            </form>

            <p className="status">{status}</p>
          </section>

          <section className="panel answer-panel">
            <h2>Answer</h2>
            <div className="answer-box">
              {answer ? <p>{answer}</p> : <p className="muted">Your answer will appear here.</p>}
            </div>
          </section>
        </div>

        <section className="sources">
          <h2>Sources</h2>
          {sources.length === 0 ? (
            <p className="muted">No sources yet.</p>
          ) : (
            <div className="source-grid">
              {sources.map((source, index) => (
                <article className="source-card" key={`${source.file_path}-${index}`}>
                  <div className="source-head">
                    <strong>{source.file_path}</strong>
                    <span>Source {index + 1}</span>
                  </div>
                  {source.section_title && <p className="source-meta">Section: {source.section_title}</p>}
                  {source.symbol_name && <p className="source-meta">Symbol: {source.symbol_name}</p>}
                  <pre>{source.snippet}</pre>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
