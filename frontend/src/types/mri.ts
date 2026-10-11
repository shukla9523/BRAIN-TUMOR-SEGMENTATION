export interface HealthResponse {
  status: string;
  model_available: boolean;
  model_version: string;
  device: string;
  pytorch_version: string;
  monai_available: boolean;
  disclaimer: string;
}

export interface ModelInfoResponse {
  architecture: string;
  version: string;
  expected_modalities: string[];
  input_spatial_shape: number[];
  label_mapping: Record<string, string>;
  evaluation_subregions: Record<string, string>;
  checkpoint_status: string;
  checkpoint_path?: string;
  parameters_count?: number;
  training_dataset: string;
  intended_use: string;
}

export interface UploadResponse {
  upload_id: string;
  filename: string;
  file_size_bytes: number;
  dimensions: number[];
  voxel_spacing: number[];
  orientation: string;
  modalities_detected: string[];
  total_slices_axial: number;
  total_slices_coronal: number;
  total_slices_sagittal: number;
  warnings: string[];
  created_at: string;
}

export interface QuantitativeRegionMetrics {
  region_id: string;
  region_name: string;
  labels_included: number[];
  volume_cm3: number;
  voxel_count: number;
  percentage_of_brain?: number;
  slice_extent_sagittal: number[];
  slice_extent_coronal: number[];
  slice_extent_axial: number[];
  connected_components: number;
  color_hex: string;
}

export interface QuantitativeReport {
  total_tumor_volume_cm3: number;
  regions: QuantitativeRegionMetrics[];
  voxel_spacing_mm: number[];
  dimensions: number[];
  processing_time_seconds: number;
  quality_warnings: string[];
  disclaimer: string;
}

export interface ResultInfo {
  result_id: string;
  upload_id: string;
  mask_path: string;
  mri_path: string;
  dimensions: number[];
  voxel_spacing: number[];
  quantitative_report: QuantitativeReport;
  created_at: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  result_id?: string;
  error?: string;
}

export interface SliceVisualizationResponse {
  result_id: string;
  slice_index: number;
  plane: 'axial' | 'coronal' | 'sagittal';
  width: number;
  height: number;
  image_base64: string;
  mask_base64?: string;
  overlay_base64: string;
  has_tumor: boolean;
  subregion_counts: {
    NCR_NET: number;
    ED: number;
    ET: number;
  };
}

export interface EpochRecord {
  epoch: number;
  train_loss: number;
  val_loss?: number;
  val_dice?: number;
  val_dice_wt?: number;
  val_dice_tc?: number;
  val_dice_et?: number;
}

export interface MetricSummaryItem {
  name: string;
  labels?: number[];
  dice_mean: number;
  dice_std?: number;
  iou_mean: number;
  iou_std?: number;
  sensitivity_mean: number;
  specificity_mean: number;
  hd95_mean_mm?: number;
}

export interface EvaluationMetricsData {
  dataset_name: string;
  evaluation_date?: string;
  total_validation_cases?: number;
  loss_function?: string;
  metrics_summary: Record<string, MetricSummaryItem>;
  epoch_history: EpochRecord[];
  held_out_comparison?: Record<string, Record<string, number>>;
  limitations_note?: string;
  status?: string;
  message?: string;
}

export interface SampleScanItem {
  sample_id: string;
  filename: string;
  description: string;
  size_bytes: number;
}
