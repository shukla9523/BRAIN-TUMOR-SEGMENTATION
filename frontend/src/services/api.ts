import {
  HealthResponse,
  ModelInfoResponse,
  UploadResponse,
  JobStatusResponse,
  ResultInfo,
  SliceVisualizationResponse,
  EvaluationMetricsData,
  SampleScanItem
} from '../types/mri';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api';

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  async getModelInfo(): Promise<ModelInfoResponse> {
    const res = await fetch(`${API_BASE}/model-info`);
    if (!res.ok) throw new Error(`Failed to fetch model info: ${res.statusText}`);
    return res.json();
  },

  async uploadMri(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async startSegmentation(uploadId: string, modality: string = 'FLAIR'): Promise<{ job_id: string; message: string }> {
    const res = await fetch(`${API_BASE}/segment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        upload_id: uploadId,
        selected_modality: modality,
        run_quantitative_analysis: true
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Segmentation initiation failed');
    }
    return res.json();
  },

  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error(`Job status error: ${res.statusText}`);
    return res.json();
  },

  async getResult(resultId: string): Promise<ResultInfo> {
    const res = await fetch(`${API_BASE}/results/${resultId}`);
    if (!res.ok) throw new Error(`Result fetch failed: ${res.statusText}`);
    return res.json();
  },

  async getResultSlice(
    resultId: string,
    sliceIndex: number,
    plane: 'axial' | 'coronal' | 'sagittal' = 'axial',
    alpha: number = 0.65
  ): Promise<SliceVisualizationResponse> {
    const res = await fetch(
      `${API_BASE}/results/${resultId}/slice/${sliceIndex}?plane=${plane}&alpha=${alpha}`
    );
    if (!res.ok) throw new Error(`Slice visualization error: ${res.statusText}`);
    return res.json();
  },

  async getUploadSlice(
    uploadId: string,
    sliceIndex: number,
    plane: 'axial' | 'coronal' | 'sagittal' = 'axial'
  ): Promise<SliceVisualizationResponse> {
    const res = await fetch(
      `${API_BASE}/uploads/${uploadId}/slice/${sliceIndex}?plane=${plane}`
    );
    if (!res.ok) throw new Error(`Preview slice error: ${res.statusText}`);
    return res.json();
  },

  async getMetrics(): Promise<EvaluationMetricsData> {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error(`Metrics fetch failed: ${res.statusText}`);
    return res.json();
  },

  async getSampleScans(): Promise<{ samples: SampleScanItem[] }> {
    const res = await fetch(`${API_BASE}/sample-scans`);
    if (!res.ok) throw new Error(`Failed to list sample scans: ${res.statusText}`);
    return res.json();
  },

  async loadSampleScan(sampleId: string): Promise<UploadResponse> {
    const res = await fetch(`${API_BASE}/sample-scans/load/${sampleId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to load sample scan');
    }
    return res.json();
  },

  getMaskDownloadUrl(resultId: string): string {
    return `${API_BASE}/results/${resultId}/mask`;
  },

  getReportDownloadUrl(resultId: string): string {
    return `${API_BASE}/results/${resultId}/report`;
  }
};
