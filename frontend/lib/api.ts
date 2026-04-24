const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function parseError(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return data.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function createRepo(githubUrl: string) {
  const response = await fetch(`${API_BASE_URL}/repos/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ github_url: githubUrl }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to create repository"));
  }

  return response.json();
}

export async function indexRepo(repoId: string) {
  const response = await fetch(`${API_BASE_URL}/indexing/${repoId}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to index repository"));
  }

  return response.json();
}

export async function askQuestion(repoId: string, question: string) {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repo_id: repoId, question }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to ask question"));
  }

  return response.json();
}
