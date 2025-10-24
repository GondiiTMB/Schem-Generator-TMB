import { useEffect, useState } from 'react';
import { Button, FileButton, Group, NumberInput, Stack, TagsInput, Textarea, Text, ScrollArea, Badge } from '@mantine/core';
import axios from 'axios';
import { useViewerStore } from '../hooks/useViewerStore';

interface DatasetItem {
  id: number;
  filename: string;
  original_name: string;
  format: string;
  tags: string[];
  description?: string;
}

interface TrainingRun {
  run_id: number;
  status: string;
  started_at: string;
  finished_at?: string | null;
  metrics: Record<string, unknown>;
}

export function TrainingPanel() {
  const [dataset, setDataset] = useState<DatasetItem[]>([]);
  const [trainingRuns, setTrainingRuns] = useState<TrainingRun[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [description, setDescription] = useState('');
  const [epochs, setEpochs] = useState(5);
  const [batchSize, setBatchSize] = useState(4);
  const [learningRate, setLearningRate] = useState(0.001);
  const { setSelectedFile, touch } = useViewerStore();

  const loadDataset = async () => {
    const response = await axios.get('/api/dataset');
    setDataset(response.data);
  };

  const loadTrainingRuns = async () => {
    const response = await axios.get('/api/training/status');
    setTrainingRuns(response.data.runs);
  };

  useEffect(() => {
    void loadDataset();
    void loadTrainingRuns();
  }, []);

  const handleUpload = async (file: File | null) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tags', selectedTags.join(','));
    formData.append('description', description);
    await axios.post('/api/dataset', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    setSelectedTags([]);
    setDescription('');
    await loadDataset();
  };

  const handleStartTraining = async () => {
    await axios.post('/api/training/start', {
      epochs,
      batch_size: batchSize,
      learning_rate: learningRate
    });
    await loadTrainingRuns();
  };

  return (
    <Stack gap="lg" className="panel">
      <Group align="flex-end" wrap="wrap" gap="md">
        <FileButton onChange={handleUpload} accept=".schem,.schematic,.litematic">
          {(props) => <Button {...props}>Upload Schematics</Button>}
        </FileButton>
        <TagsInput
          label="Tags"
          placeholder="Add tags"
          value={selectedTags}
          onChange={setSelectedTags}
        />
        <Textarea
          label="Description"
          value={description}
          minRows={2}
          onChange={(event) => setDescription(event.currentTarget.value)}
        />
      </Group>
      <Group gap="md" grow>
        <NumberInput label="Epochs" min={1} value={epochs} onChange={(value) => setEpochs(Number(value) || 1)} />
        <NumberInput label="Batch size" min={1} value={batchSize} onChange={(value) => setBatchSize(Number(value) || 1)} />
        <NumberInput
          label="Learning rate"
          precision={4}
          min={0.0001}
          value={learningRate}
          step={0.0005}
          onChange={(value) => setLearningRate(Number(value) || 0.0001)}
        />
        <Button onClick={handleStartTraining}>Start Training</Button>
      </Group>
      <ScrollArea h={260} className="dataset-list">
        {dataset.map((item) => (
          <Group key={item.id} className="dataset-item" justify="space-between">
            <div>
              <Text className="dataset-title">{item.original_name}</Text>
              <Text size="sm" c="dimmed">{item.tags.join(', ') || 'No tags'} · {item.format}</Text>
            </div>
            <Group gap="xs">
              <Button
                variant="subtle"
                onClick={() => {
                  setSelectedFile({ source: 'dataset', id: item.id, filename: item.filename });
                  touch();
                }}
              >
                Preview
              </Button>
              <Button component="a" href={`/api/dataset/${item.id}/download`} variant="light">
                Download
              </Button>
            </Group>
          </Group>
        ))}
      </ScrollArea>
      <Stack gap="sm">
        <Text className="dataset-title">Training Runs</Text>
        {trainingRuns.length === 0 && <Text size="sm" c="dimmed">No training runs yet.</Text>}
        {trainingRuns.map((run) => (
          <Group key={run.run_id} justify="space-between" className="dataset-item">
            <div>
              <Text size="sm">Run #{run.run_id}</Text>
              <Text size="sm" c="dimmed">Started at: {new Date(run.started_at).toLocaleString()}</Text>
            </div>
            <Badge color={run.status === 'completed' ? 'green' : 'yellow'}>{run.status}</Badge>
          </Group>
        ))}
      </Stack>
    </Stack>
  );
}
