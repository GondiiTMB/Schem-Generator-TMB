import { useState } from 'react';
import { Button, Group, Select, Stack, Textarea, Text } from '@mantine/core';
import { IconDownload, IconRefresh } from '@tabler/icons-react';
import axios from 'axios';
import { useViewerStore } from '../hooks/useViewerStore';

const FORMAT_OPTIONS = [
  { value: 'schem', label: '.schem' },
  { value: 'schematic', label: '.schematic' },
  { value: 'litematic', label: '.litematic' }
];

interface GenerationPanelProps {
  onShowViewer: () => void;
}

export function GenerationPanel({ onShowViewer }: GenerationPanelProps) {
  const [prompt, setPrompt] = useState('Generate a modern villa with glass walls');
  const [format, setFormat] = useState<string>('schem');
  const [isLoading, setIsLoading] = useState(false);
  const [latestFile, setLatestFile] = useState<string | null>(null);
  const { setSelectedFile, touch } = useViewerStore();

  const handleGenerate = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post('/api/generate', { prompt, format });
      const filename = response.data.filename as string;
      setLatestFile(filename);
      setSelectedFile({ source: 'generated', filename });
      touch();
      onShowViewer();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Stack gap="lg" className="panel">
      <Textarea
        label="Prompt"
        minRows={4}
        value={prompt}
        onChange={(event) => setPrompt(event.currentTarget.value)}
      />
      <Group gap="md">
        <Select label="Export format" data={FORMAT_OPTIONS} value={format} onChange={(value) => setFormat(value || 'schem')} />
        <Button leftSection={<IconRefresh size={18} />} loading={isLoading} onClick={handleGenerate}>
          Generate
        </Button>
        {latestFile && (
          <Button
            component="a"
            href={`/api/generate/download/${latestFile}`}
            leftSection={<IconDownload size={18} />}
            variant="light"
          >
            Download
          </Button>
        )}
      </Group>
      {latestFile && <Text className="hint">Viewer will refresh automatically after each generation.</Text>}
    </Stack>
  );
}
