import { useState } from 'react';
import { DownloadIcon, LightningBoltIcon } from './Icons';
import SchematicViewer, { SchematicData } from '../viewer/SchematicViewer';

const formats = [
  { label: '.schem (WorldEdit)', value: 'schem' },
  { label: '.schematic (Legacy)', value: 'schematic' },
  { label: '.litematic (Litematica)', value: 'litematic' },
];

export default function GenerationTab() {
  const [prompt, setPrompt] = useState('Generate a modern villa with glass walls and rooftop garden');
  const [format, setFormat] = useState('schem');
  const [targetSize, setTargetSize] = useState<[number, number, number]>([32, 32, 32]);
  const [viewerData, setViewerData] = useState<SchematicData | null>(null);
  const [downloadPath, setDownloadPath] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, output_format: format, target_size: targetSize }),
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || 'Failed to generate structure');
      }
      const payload = await response.json();
      setViewerData(payload.viewer_data);
      setDownloadPath(payload.file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!downloadPath) return;
    const url = downloadPath.startsWith('http') ? downloadPath : `${downloadPath}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = url.split('/').pop() ?? 'generated.schem';
    link.click();
  };

  return (
    <section className="grid gap-8 lg:grid-cols-[420px,1fr]">
      <div className="panel space-y-6">
        <div className="space-y-3">
          <label className="text-sm uppercase tracking-widest text-white/60">Prompt</label>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={4}
            placeholder="Describe the structure you want to build"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <label className="text-sm uppercase tracking-widest text-white/60">Export format</label>
            <select value={format} onChange={(event) => setFormat(event.target.value)}>
              {formats.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label className="text-sm uppercase tracking-widest text-white/60">Target size</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={targetSize[0]}
                onChange={(event) => setTargetSize([Number(event.target.value), targetSize[1], targetSize[2]])}
                className="w-20"
                min={8}
                max={64}
              />
              <span className="text-white/40">×</span>
              <input
                type="number"
                value={targetSize[1]}
                onChange={(event) => setTargetSize([targetSize[0], Number(event.target.value), targetSize[2]])}
                className="w-20"
                min={8}
                max={64}
              />
              <span className="text-white/40">×</span>
              <input
                type="number"
                value={targetSize[2]}
                onChange={(event) => setTargetSize([targetSize[0], targetSize[1], Number(event.target.value)])}
                className="w-20"
                min={8}
                max={64}
              />
            </div>
          </div>
        </div>

        {error ? <p className="text-red-400 text-sm">{error}</p> : null}

        <div className="flex gap-3">
          <button className="button-primary flex items-center gap-2" onClick={handleGenerate} disabled={isGenerating}>
            <LightningBoltIcon className={isGenerating ? 'animate-spin' : ''} />
            {isGenerating ? 'Generating…' : 'Generate'}
          </button>
          <button
            className="button-primary flex items-center gap-2 bg-white/10 text-white hover:-translate-y-1 hover:bg-white/20"
            onClick={handleDownload}
            disabled={!downloadPath}
          >
            <DownloadIcon />
            Download
          </button>
        </div>
      </div>

      <div className="panel min-h-[520px]">
        <h2 className="text-lg font-semibold mb-4 text-white/80 flex items-center justify-between">
          3D Preview
          <span className="text-sm text-white/40">Live renderer with orbit + layer controls</span>
        </h2>
        <SchematicViewer data={viewerData ?? undefined} />
      </div>
    </section>
  );
}
