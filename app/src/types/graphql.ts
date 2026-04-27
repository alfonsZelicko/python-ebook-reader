// TypeScript types mirroring the GraphQL schema

export type FieldType = "string" | "number" | "boolean" | "select" | "file";

export interface ParameterMeta {
  name: string;
  label: string;
  fieldType: FieldType;
  choices?: string[];
  accept?: string; // e.g. ".wav" — only for fieldType === 'file'
  defaultValue?: string; // JSON-serialized default
  helpText?: string;
  required: boolean;
}

export interface EngineDetail {
  name: string;
  description: string;
  requiredParameters: ParameterMeta[];
  optionalParameters: ParameterMeta[];
}

export interface EngineInfo {
  ttsEngines: EngineDetail[];
  translationEngines: EngineDetail[];
}

export interface JobProgress {
  percentage: number;
  currentChunk: number;
  totalChunks: number;
  stage: string;
  estimatedTimeRemaining?: number;
}

export type JobStatusEnum = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface FileDownload {
  fileId: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  downloadUrl?: string;
  content?: string;
}

export interface TTSMetadata {
  engineUsed: string;
  totalChunks: number;
  totalDurationSeconds: number;
  outputDirectory: string;
}

export interface TranslationMetadata {
  engineUsed: string;
  sourceLanguage: string;
  targetLanguage: string;
  totalChunks: number;
  outputDirectory: string;
}

export interface TTSResultWithFile {
  success: boolean;
  message: string;
  outputFiles: string[];
  metadata: TTSMetadata;
  fileDownload?: FileDownload;
}

export interface TranslationResultWithFile {
  success: boolean;
  message: string;
  outputFile: string;
  metadata: TranslationMetadata;
  fileDownload?: FileDownload;
}

export interface JobCreated {
  jobId: string;
  message: string;
}

export interface JobStatus {
  jobId: string;
  status: JobStatusEnum;
  progress: JobProgress;
  result?: TTSResultWithFile | TranslationResultWithFile;
  error?: string;
}
