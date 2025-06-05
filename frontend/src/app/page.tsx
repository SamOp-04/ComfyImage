"use client";

import PromptStream from "@/components/PromptStream";
import UpscaleStream from "@/components/UpscaleStream";
import { useState } from "react";

const workflows = [
  { id: "real", label: "Generate Real Image" },
  { id: "anime", label: "Generate Anime Image" },
  { id: "upscale", label: "Upscale Your Image" },
];

export default function HomePage() {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  if (selectedWorkflow) {
    // Dynamically render the component for the workflow
    switch (selectedWorkflow) {
      case "real":
        return <GeneratePage workflow="real" onBack={() => setSelectedWorkflow(null)} />;
      case "anime":
        return <GeneratePage workflow="anime" onBack={() => setSelectedWorkflow(null)} />;
      case "upscale":
        return <UpscalePage onBack={() => setSelectedWorkflow(null)} />;
      default:
        return null;
    }
  }

  return (
    <main className="p-6 max-w-lg mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-center">Welcome to ComfyImage!</h1>
      <p className="mb-4 text-center text-gray-700">
        Choose an option below to get started:
      </p>
      <div className="space-y-4">
        {workflows.map((w) => (
          <button
            key={w.id}
            onClick={() => setSelectedWorkflow(w.id)}
            className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 transition"
          >
            {w.label}
          </button>
        ))}
      </div>
    </main>
  );
}

// --- Generic generate page for real / anime workflows ---
function GeneratePage({
  workflow,
  onBack,
}: {
  workflow: string;
  onBack: () => void;
}) {
  // reuse PromptStream component but pass workflow prop to choose workflow file

  return (
    <div className="p-6 max-w-md mx-auto">
      <button
        onClick={onBack}
        className="mb-4 text-blue-600 underline"
      >
        ← Back to Home
      </button>
      <h2 className="text-xl font-semibold mb-4 capitalize">{workflow} Image Generator</h2>
      <PromptStream workflow={workflow} />
    </div>
  );
}

// --- Upscale page allows image upload ---
function UpscalePage({ onBack }: { onBack: () => void }) {
  return (
    <div className="p-6 max-w-md mx-auto">
      <button
        onClick={onBack}
        className="mb-4 text-blue-600 underline"
      >
        ← Back to Home
      </button>
      <h2 className="text-xl font-semibold mb-4">Upscale Your Image</h2>
      <UpscaleStream />
    </div>
  );
}
