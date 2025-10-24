export type CropRegion = {
  min: [number, number, number];
  max: [number, number, number] | null;
};

export type DatasetEntry = {
  id: string;
  filename: string;
  original_name: string;
  size: [number, number, number];
  format: string;
  tags: string[];
  description: string;
  crop_region: CropRegion;
};

export type TrainingStatus = {
  active: boolean;
  current_epoch: number;
  total_epochs: number;
  loss: number;
};

export type ViewerData = {
  palette: string[];
  blocks: number[][][];
  size: [number, number, number];
};
