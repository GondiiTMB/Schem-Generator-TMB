import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export type SchematicData = {
  palette: string[];
  blocks: number[][][];
  size: [number, number, number];
};

type RendererApi = {
  load: (data: SchematicData) => void;
  dispose: () => void;
  setLayerRange: (range: [number, number]) => void;
};

class FallbackRenderer implements RendererApi {
  private container: HTMLElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private animationId: number | null = null;
  private group: THREE.Group;
  private currentData: SchematicData | null = null;
  private layerRange: [number, number] = [0, Infinity];

  constructor(container: HTMLElement) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#0c0f16');
    const { clientWidth, clientHeight } = container;
    this.camera = new THREE.PerspectiveCamera(60, clientWidth / clientHeight, 0.1, 1000);
    this.camera.position.set(40, 40, 40);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(clientWidth, clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.group = new THREE.Group();
    this.scene.add(this.group);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight.position.set(60, 100, 80);
    this.scene.add(dirLight);
    window.addEventListener('resize', this.handleResize);
    this.animate();
  }

  private animate = () => {
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.animationId = requestAnimationFrame(this.animate);
  };

  private handleResize = () => {
    const { clientWidth, clientHeight } = this.container;
    this.camera.aspect = clientWidth / Math.max(clientHeight, 1);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(clientWidth, clientHeight);
  };

  load(data: SchematicData) {
    this.currentData = data;
    this.group.clear();
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const materials: THREE.Material[] = [];
    const colorForBlock = (blockName: string) => {
      if (blockName.includes('glass')) return '#8ecae6';
      if (blockName.includes('stone')) return '#adb5bd';
      if (blockName.includes('wood') || blockName.includes('log')) return '#b08968';
      if (blockName.includes('brick')) return '#b52b3a';
      if (blockName.includes('leaf') || blockName.includes('leaves')) return '#8fbf3d';
      if (blockName.includes('water')) return '#357ded';
      if (blockName.includes('sand')) return '#f4d35e';
      if (blockName.includes('grass')) return '#7ec850';
      return '#d9d9d9';
    };
    const [width, height, length] = data.size;
    for (let y = 0; y < height; y += 1) {
      for (let z = 0; z < length; z += 1) {
        for (let x = 0; x < width; x += 1) {
          const paletteIndex = data.blocks[y][z][x];
          const blockName = data.palette[paletteIndex];
          if (!blockName || blockName.includes('air')) continue;
          if (!materials[paletteIndex]) {
            const material = new THREE.MeshStandardMaterial({
              color: new THREE.Color(colorForBlock(blockName)),
            });
            materials[paletteIndex] = material;
          }
          const cube = new THREE.Mesh(geometry, materials[paletteIndex]);
          cube.position.set(x - width / 2, y, z - length / 2);
          cube.userData = { y };
          this.group.add(cube);
        }
      }
    }
    this.setLayerRange(this.layerRange);
    const bounding = new THREE.Box3().setFromObject(this.group);
    const center = new THREE.Vector3();
    bounding.getCenter(center);
    this.controls.target.copy(center);
  }

  setLayerRange(range: [number, number]) {
    this.layerRange = range;
    this.group.children.forEach((child) => {
      const y = (child as THREE.Mesh).userData?.y ?? 0;
      child.visible = y >= range[0] && y <= range[1];
    });
  }

  dispose() {
    window.removeEventListener('resize', this.handleResize);
    if (this.animationId) cancelAnimationFrame(this.animationId);
    this.renderer.dispose();
    this.controls.dispose();
    this.group.clear();
    this.container.removeChild(this.renderer.domElement);
  }
}

async function createRenderer(container: HTMLElement): Promise<RendererApi> {
  try {
    const module: any = await import('schematic-renderer');
    const RendererClass = module?.SchematicRenderer ?? module?.default;
    if (RendererClass) {
      const instance = new RendererClass(container, { background: '#0c0f16' });
      return {
        load(data: SchematicData) {
          if (typeof instance.load === 'function') {
            instance.load(data);
          } else if (typeof instance.render === 'function') {
            instance.render(data);
          }
        },
        dispose() {
          instance.dispose?.();
        },
        setLayerRange(range: [number, number]) {
          if (typeof instance.setLayerRange === 'function') {
            instance.setLayerRange(range[0], range[1]);
          }
        },
      } satisfies RendererApi;
    }
  } catch (error) {
    console.warn('Falling back to internal renderer', error);
  }
  return new FallbackRenderer(container);
}

export default function SchematicViewer({ data }: { data?: SchematicData }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<RendererApi | null>(null);
  const [layerMax, setLayerMax] = useState(0);
  const [layerMin, setLayerMin] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    let disposed = false;
    void createRenderer(containerRef.current).then((renderer) => {
      if (disposed) {
        renderer.dispose();
        return;
      }
      rendererRef.current = renderer;
      if (data) {
        renderer.load(data);
        const height = data.size[1];
        setLayerMin(0);
        setLayerMax(Math.max(height - 1, 0));
        renderer.setLayerRange([0, Math.max(height - 1, 0)]);
      }
    });
    return () => {
      disposed = true;
      rendererRef.current?.dispose();
      rendererRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (data && rendererRef.current) {
      rendererRef.current.load(data);
      const height = data.size[1];
      const maxLayer = Math.max(height - 1, 0);
      setLayerMin(0);
      setLayerMax(maxLayer);
      rendererRef.current.setLayerRange([0, maxLayer]);
    }
  }, [data]);

  useEffect(() => {
    if (rendererRef.current) {
      rendererRef.current.setLayerRange([layerMin, layerMax]);
    }
  }, [layerMin, layerMax]);

  return (
    <div className="h-full w-full flex flex-col gap-4">
      <div ref={containerRef} className="flex-1 rounded-2xl bg-black/30 overflow-hidden" />
      <div className="flex gap-4 text-xs items-center">
        <label className="flex flex-col gap-1">
          Min Layer
          <input
            type="range"
            min={0}
            max={Math.max(layerMax, 0)}
            value={layerMin}
            onChange={(event) => setLayerMin(Number(event.target.value))}
          />
        </label>
        <label className="flex flex-col gap-1">
          Max Layer
          <input
            type="range"
            min={layerMin}
            max={data ? Math.max(data.size[1] - 1, layerMin) : 64}
            value={layerMax}
            onChange={(event) => setLayerMax(Number(event.target.value))}
          />
        </label>
      </div>
    </div>
  );
}
