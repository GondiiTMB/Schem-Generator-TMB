import { useEffect, useRef } from 'react';
import { Alert, Group, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import axios from 'axios';
import { useViewerStore } from '../hooks/useViewerStore';

// @ts-expect-error - schematic-renderer lacks type definitions
import { SchematicRenderer } from 'schematic-renderer';

export function ViewerPanel() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<any>(null);
  const { selectedFile, lastUpdated } = useViewerStore();

  useEffect(() => {
    if (!containerRef.current) return;
    if (!rendererRef.current) {
      rendererRef.current = new SchematicRenderer({
        target: containerRef.current,
        enableLayerControl: true,
        enableGrid: true
      });
    }
  }, []);

  useEffect(() => {
    const load = async () => {
      if (!selectedFile || !rendererRef.current) return;
      let response;
      if (selectedFile.source === 'generated') {
        response = await axios.get(`/api/generate/download/${selectedFile.filename}`, { responseType: 'arraybuffer' });
      } else {
        response = await axios.get(`/api/dataset/${selectedFile.id}/viewer`, { responseType: 'arraybuffer' });
      }
      const blob = new Blob([response.data]);
      await rendererRef.current.loadSchematic(blob);
    };
    void load();
  }, [selectedFile, lastUpdated]);

  if (!selectedFile) {
    return (
      <Alert icon={<IconInfoCircle size={16} />} title="No schematic selected">
        Select a generated or uploaded schematic to preview it in 3D.
      </Alert>
    );
  }

  const name = selectedFile.filename;

  return (
    <Stack>
      <Group justify="space-between">
        <Text className="viewer-title">Previewing {name}</Text>
      </Group>
      <div ref={containerRef} className="viewer-canvas" />
    </Stack>
  );
}
