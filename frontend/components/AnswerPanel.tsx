type Props = {
  answer: string;
};

export default function AnswerPanel({ answer }: Props) {
  return (
    <div className="rounded-xl border p-4">
      <h2 className="mb-2 text-xl font-semibold">Answer</h2>
      <p className="whitespace-pre-wrap text-gray-800">
        {answer || "No answer yet."}
      </p>
    </div>
  );
}