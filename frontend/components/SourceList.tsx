type Source = {
  file_path: string;
  section_title?: string | null;
  symbol_name?: string | null;
  snippet: string;
};

type Props = {
  sources: Source[];
};

export default function SourceList({ sources }: Props) {
  return (
    <div className="rounded-xl border p-4">
      <h2 className="mb-3 text-xl font-semibold">Sources</h2>
      {sources.length === 0 ? (
        <p className="text-gray-600">No sources yet.</p>
      ) : (
        <div className="space-y-4">
          {sources.map((source, index) => (
            <div key={index} className="rounded-md border p-3">
              <p className="font-medium">{source.file_path}</p>
              {source.section_title && (
                <p className="text-sm text-gray-600">
                  Section: {source.section_title}
                </p>
              )}
              {source.symbol_name && (
                <p className="text-sm text-gray-600">
                  Symbol: {source.symbol_name}
                </p>
              )}
              <pre className="mt-2 whitespace-pre-wrap text-sm text-gray-800">
                {source.snippet}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}