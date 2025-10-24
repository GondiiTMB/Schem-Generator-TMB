import '@fontsource/minecraft/400.css';
import { useState } from 'react';
import GenerationTab from './components/GenerationTab';
import TrainingTab from './components/TrainingTab';

type TabKey = 'generate' | 'train';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('generate');

  return (
    <div className="min-h-screen px-6 py-10 md:px-16 md:py-12">
      <header className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="floating">
          <h1 className="text-4xl md:text-5xl font-bold tracking-wide">
            Minecraft AI Structure Generator
          </h1>
          <p className="text-white/70 mt-3 max-w-2xl">
            Generate, preview, and train custom Minecraft structures completely locally. Upload your
            schematics, fine-tune the AI, and render creations instantly in the browser.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            className={`tab-button ${activeTab === 'generate' ? 'tab-button-active' : 'tab-button-inactive'}`}
            onClick={() => setActiveTab('generate')}
          >
            Generation Studio
          </button>
          <button
            className={`tab-button ${activeTab === 'train' ? 'tab-button-active' : 'tab-button-inactive'}`}
            onClick={() => setActiveTab('train')}
          >
            Training Lab
          </button>
        </div>
      </header>

      <main className="mt-10">
        {activeTab === 'generate' ? <GenerationTab /> : <TrainingTab />}
      </main>
    </div>
  );
}
