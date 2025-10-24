declare module 'schematic-renderer' {
  export class SchematicRenderer {
    constructor(container: HTMLElement, options?: Record<string, unknown>);
    load(data: unknown): void;
    render?(data: unknown): void;
    dispose?(): void;
    setLayerRange?(min: number, max: number): void;
  }
}
