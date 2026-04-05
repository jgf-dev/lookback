import { Card } from "@/components/ui/card";

export default function ReviewPage() {
  return (
    <main>
      <h1>End-of-Day Review</h1>
      <Card title="Summary">
        <p>Highlights, blockers, and next actions will appear here.</p>
      </Card>
      <Card title="Insights">
        <p>Insight cards generated from captured events.</p>
      </Card>
    </main>
  );
}
