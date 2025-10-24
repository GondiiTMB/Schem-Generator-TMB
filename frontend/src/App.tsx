import { useState } from 'react';
import { MantineProvider, AppShell, Tabs, Group, Title } from '@mantine/core';
import { GenerationPanel } from './components/GenerationPanel';
import { TrainingPanel } from './components/TrainingPanel';
import { ViewerPanel } from './components/ViewerPanel';
import { useViewerStore } from './hooks/useViewerStore';

export default function App() {
  const [activeTab, setActiveTab] = useState<string | null>('generate');
  const { selectedFile } = useViewerStore();

  return (
    <MantineProvider defaultColorScheme="dark" theme={{ fontFamily: 'Minecraft, sans-serif' }}>
      <AppShell padding="md">
        <AppShell.Header>
          <Group justify="space-between" px="lg" py="sm">
            <Title order={2} className="app-title">Minecraft AI Structure Generator</Title>
          </Group>
        </AppShell.Header>
        <AppShell.Main>
          <Tabs value={activeTab} onChange={setActiveTab} keepMounted={false}>
            <Tabs.List className="app-tabs">
              <Tabs.Tab value="generate">Generation</Tabs.Tab>
              <Tabs.Tab value="train">Training</Tabs.Tab>
              <Tabs.Tab value="viewer" disabled={!selectedFile}>Viewer</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel value="generate">
              <GenerationPanel onShowViewer={() => setActiveTab('viewer')} />
            </Tabs.Panel>
            <Tabs.Panel value="train">
              <TrainingPanel />
            </Tabs.Panel>
            <Tabs.Panel value="viewer">
              <ViewerPanel />
            </Tabs.Panel>
          </Tabs>
        </AppShell.Main>
      </AppShell>
    </MantineProvider>
  );
}
