import { useEffect, useMemo, useState } from 'react';
import { DatasetEntry, TrainingStatus, ViewerData } from '../types/api';
import { RefreshIcon, UploadIcon } from './Icons';
import SchematicViewer from '../viewer/SchematicViewer';

const defaultTraining = {
  epochs: 15,
  batchSize: 2,
  learningRate: 0.001,
  targetSize: [32, 32, 32] as [number, number, number],
};

export default function TrainingTab() {
  const [entries, setEntries] = useState<DatasetEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewerData, setViewerData] = useState<ViewerData | undefined>(undefined);
  const [tagsInput, setTagsInput] = useState('');
  const [description, setDescription] = useState('');
  const [cropMin, setCropMin] = useState<[number, number, number]>([0, 0, 0]);
  const [cropMax, setCropMax] = useState<[number, number, number]>([0, 0, 0]);
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [uploading, setUploading] = useState(false);
  const [trainingConfig, setTrainingConfig] = useState(defaultTraining);
  const [message, setMessage] = useState<string | null>(null);

  const selectedEntry = useMemo(() => entries.find((entry) => entry.id === selectedId) ?? null, [entries, selectedId]);

  const refreshEntries = async () => {
    const response = await fetch('/api/dataset');
    const data = await response.json();
    setEntries(data);
    if (data.length) {
      const stillExists = selectedId && data.some((entry: DatasetEntry) => entry.id === selectedId);
      if (!stillExists) {
        setSelectedId(data[0].id);
      }
    }
  };

  useEffect(() => {
    void refreshEntries();
  }, []);

  useEffect(() => {
    if (!selectedEntry) return;
    setTagsInput(selectedEntry.tags.join(', '));
    setDescription(selectedEntry.description);
    const max = selectedEntry.crop_region.max ?? [selectedEntry.size[0], selectedEntry.size[1], selectedEntry.size[2]];
    setCropMin(selectedEntry.crop_region.min);
    setCropMax(max as [number, number, number]);
    const loadViewer = async () => {
      const response = await fetch(`/api/dataset/${selectedEntry.id}/viewer`);
      const json = await response.json();
      setViewerData(json);
    };
    void loadViewer();
  }, [selectedEntry]);

  useEffect(() => {
    const timer = setInterval(async () => {
      const response = await fetch('/api/train/status');
      const json = await response.json();
      setStatus(json);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || !files.length) return;
    setUploading(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append('file', files[0]);
      const response = await fetch('/api/dataset/upload', {
        method: 'POST',
        body: form,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await refreshEntries();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleSaveMetadata = async () => {
    if (!selectedEntry) return;
    setMessage(null);
    const fullMax: [number, number, number] = [selectedEntry.size[0], selectedEntry.size[1], selectedEntry.size[2]];
    const isFullSelection =
      cropMin.every((value, index) => value === 0) && cropMax.every((value, index) => value >= fullMax[index]);
    const payload = {
      tags: tagsInput.split(',').map((tag) => tag.trim()).filter(Boolean),
      description,
      crop_region: {
        min: cropMin,
        max: isFullSelection ? null : cropMax,
      },
    };
    const response = await fetch(`/api/dataset/${selectedEntry.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setMessage('Failed to save metadata');
      return;
    }
    setMessage('Metadata saved');
    await refreshEntries();
  };

  const handleStartTraining = async () => {
    setMessage(null);
    const response = await fetch('/api/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        epochs: trainingConfig.epochs,
        batch_size: trainingConfig.batchSize,
        learning_rate: trainingConfig.learningRate,
        target_size: trainingConfig.targetSize,
      }),
    });
    if (!response.ok) {
      setMessage('Training failed to start');
      return;
    }
    const json = await response.json();
    setStatus(json);
    setMessage('Training started');
  };

  const handleCropChange = (
    axis: 0 | 1 | 2,
    type: 'min' | 'max',
    value: number,
  ) => {
    const clampValue = (val: number) => Math.max(0, Math.min(val, selectedEntry ? selectedEntry.size[axis] : val));
    if (type === 'min') {
      const next = [...cropMin] as [number, number, number];
      next[axis] = clampValue(value);
      setCropMin(next);
      if (cropMax[axis] <= next[axis]) {
        const updatedMax = [...cropMax] as [number, number, number];
        updatedMax[axis] = next[axis] + 1;
        setCropMax(updatedMax);
      }
    } else {
      const next = [...cropMax] as [number, number, number];
      next[axis] = clampValue(value);
      setCropMax(next);
      if (next[axis] <= cropMin[axis]) {
        const updatedMin = [...cropMin] as [number, number, number];
        updatedMin[axis] = Math.max(0, next[axis] - 1);
        setCropMin(updatedMin);
      }
    }
  };

  return (
    <section className="grid gap-8 xl:grid-cols-[360px,1fr]">
      <div className="panel space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Dataset</h2>
          <label className="button-primary flex items-center gap-2 cursor-pointer">
            <UploadIcon /> Upload
            <input type="file" accept=".schem,.schematic,.litematic" className="hidden" onChange={handleFileUpload} />
          </label>
        </div>
        {uploading ? <p className="text-sm text-white/60">Uploading…</p> : null}
        <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
          {entries.map((entry) => (
            <button
              key={entry.id}
              onClick={() => setSelectedId(entry.id)}
              className={`w-full text-left p-4 rounded-2xl transition ${
                selectedId === entry.id ? 'bg-accent/20 border border-accent/40' : 'bg-white/5 hover:bg-white/10'
              }`}
            >
              <p className="font-semibold">{entry.original_name}</p>
              <p className="text-xs text-white/50 mt-1">
                {entry.size.join(' × ')} · {entry.format.toUpperCase()}
              </p>
            </button>
          ))}
          {!entries.length ? <p className="text-white/50 text-sm">Upload schematics to begin training.</p> : null}
        </div>

        {selectedEntry ? (
          <div className="space-y-4">
            <div>
              <label className="text-xs uppercase tracking-widest text-white/50">Tags</label>
              <input value={tagsInput} onChange={(event) => setTagsInput(event.target.value)} placeholder="castle, tower" />
            </div>
            <div>
              <label className="text-xs uppercase tracking-widest text-white/50">Description</label>
              <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} />
            </div>

            <div className="grid grid-cols-3 gap-3">
              {(['X', 'Y', 'Z'] as const).map((axisLabel, index) => (
                <div key={axisLabel} className="space-y-2">
                  <p className="text-xs text-white/50">{axisLabel} Min</p>
                  <input
                    type="number"
                    value={cropMin[index]}
                    min={0}
                    max={selectedEntry.size[index]}
                    onChange={(event) => handleCropChange(index as 0 | 1 | 2, 'min', Number(event.target.value))}
                  />
                  <p className="text-xs text-white/50">{axisLabel} Max</p>
                  <input
                    type="number"
                    value={cropMax[index]}
                    min={cropMin[index] + 1}
                    max={selectedEntry.size[index]}
                    onChange={(event) => handleCropChange(index as 0 | 1 | 2, 'max', Number(event.target.value))}
                  />
                </div>
              ))}
            </div>

            <button className="button-primary w-full" onClick={handleSaveMetadata}>
              Save metadata & crop
            </button>
          </div>
        ) : null}

        <div className="space-y-3 pt-4 border-t border-white/10">
          <h3 className="font-semibold">Training configuration</h3>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs text-white/50">
              Epochs
              <input
                type="number"
                value={trainingConfig.epochs}
                min={1}
                max={200}
                onChange={(event) => setTrainingConfig((prev) => ({ ...prev, epochs: Number(event.target.value) }))}
              />
            </label>
            <label className="text-xs text-white/50">
              Batch size
              <input
                type="number"
                value={trainingConfig.batchSize}
                min={1}
                max={32}
                onChange={(event) => setTrainingConfig((prev) => ({ ...prev, batchSize: Number(event.target.value) }))}
              />
            </label>
            <label className="text-xs text-white/50">
              Learning rate
              <input
                type="number"
                step="0.0001"
                value={trainingConfig.learningRate}
                onChange={(event) => setTrainingConfig((prev) => ({ ...prev, learningRate: Number(event.target.value) }))}
              />
            </label>
            <label className="text-xs text-white/50">
              Target size (Y×Z×X)
              <div className="flex gap-2 mt-1">
                {trainingConfig.targetSize.map((value, index) => (
                  <input
                    key={index}
                    type="number"
                    value={value}
                    min={8}
                    max={64}
                    className="w-16"
                    onChange={(event) => {
                      const next = [...trainingConfig.targetSize] as [number, number, number];
                      next[index] = Number(event.target.value);
                      setTrainingConfig((prev) => ({ ...prev, targetSize: next }));
                    }}
                  />
                ))}
              </div>
            </label>
          </div>
          <button className="button-primary w-full" onClick={handleStartTraining}>
            Start training
          </button>
          {status ? (
            <p className="text-xs text-white/60">
              {status.active ? 'Training…' : 'Idle'} · Epoch {status.current_epoch}/{status.total_epochs} · Loss {status.loss.toFixed(4)}
            </p>
          ) : null}
        </div>
        {message ? <p className="text-xs text-accent">{message}</p> : null}
      </div>

      <div className="panel min-h-[560px] space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Schematic inspector</h2>
            {selectedEntry ? (
              <p className="text-xs text-white/50">{selectedEntry.original_name}</p>
            ) : (
              <p className="text-xs text-white/50">Select a schematic to preview</p>
            )}
          </div>
          <button className="text-white/60 hover:text-white transition" onClick={() => selectedEntry && setSelectedId(selectedEntry.id)}>
            <RefreshIcon />
          </button>
        </div>
        <SchematicViewer data={viewerData} />
      </div>
    </section>
  );
}
