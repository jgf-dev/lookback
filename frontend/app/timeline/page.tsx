import { Card } from "@/components/ui/card";
import { Filters } from "@/components/ui/filters";
import { VoiceControls } from "@/components/ui/voice-controls";

export default function TimelinePage() {
  return (
    <main>
      <h1>Timeline</h1>
      <p>Live canvas for events arriving from voice, search, and screenshots.</p>
      <Filters />
      <VoiceControls />
      <Card title="Live Canvas">
        <p>No events yet. Connect backend stream to render timeline cards here.</p>
      </Card>
    </main>
  );
}
