"use client";

import { useState } from "react";

export default function UpscaleStream() {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [showProgressMessage, setShowProgressMessage] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert("Please upload an image to upscale.");
      return;
    }

    setJobId(null);
    setShowProgressMessage(false);

    try {
      // Upload file via FormData
      const formData = new FormData();
      formData.append("workflow", "upscale");
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/generate-upscale", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setJobId(data.job_id);
      setShowProgressMessage(true);
    } catch (err: any) {
      alert("Error submitting upscale request: " + err.message);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="mb-4"
          required
        />
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded"
        >
          Upscale Image
        </button>
      </form>

      {showProgressMessage && (
        <p className="mt-4 text-center text-gray-600">
          <a
            href="http://localhost:8188/task_monitor/index.html"
            className="text-blue-500 underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            View Progress
          </a>
        </p>
      )}

      <div className="mt-4 text-center">
        <p className="mb-2 font-semibold">Resulting Image:</p>
        {jobId ? (
          <img
            src={`http://localhost:8000/image/${jobId}`}
            alt="Upscaled Image"
            className="mx-auto border rounded"
          />
        ) : (
          <p className="text-gray-500">No image upscaled yet.</p>
        )}
      </div>
    </div>
  );
}
