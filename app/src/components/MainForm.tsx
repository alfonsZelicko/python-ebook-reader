"use client";

import { useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CloseIcon from "@mui/icons-material/Close";
import { useMutation } from "@apollo/client/react";

import { EngineSelector } from "./EngineSelector";
import { DynamicForm } from "./DynamicForm";
import { JobProgress } from "./JobProgress";
import { ResultPanel } from "./ResultPanel";
import { useAvailableEngines } from "@/hooks/useAvailableEngines";
import { useJobPoller } from "@/hooks/useJobPoller";
import { GENERATE_SPEECH_MUTATION, TRANSLATE_TEXT_MUTATION } from "@/graphql/mutations";
import type {
  EngineDetail,
  JobCreated,
  ParameterMeta,
  TTSResultWithFile,
  TranslationResultWithFile,
} from "@/types/graphql";

type Mode = "translate" | "read";
type JobState = "idle" | "submitting" | "polling" | "done" | "error";

interface FormState {
  mode: Mode;
  file: File | null;
  engineName: string;
  params: Record<string, unknown>;
  jobId: string | null;
  jobState: JobState;
  errorMessage: string | null;
  ttsResult: TTSResultWithFile | null;
  translationResult: TranslationResultWithFile | null;
}

function buildDefaultParams(engine: EngineDetail): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};
  const allParams: ParameterMeta[] = [
    ...engine.requiredParameters,
    ...engine.optionalParameters,
  ];
  for (const p of allParams) {
    if (p.defaultValue !== undefined) {
      try {
        if (p.fieldType === "boolean") defaults[p.name] = JSON.parse(p.defaultValue);
        else if (p.fieldType === "number") defaults[p.name] = Number(p.defaultValue);
        else defaults[p.name] = p.defaultValue;
      } catch {
        defaults[p.name] = p.defaultValue;
      }
    }
  }
  return defaults;
}

export function MainForm() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { ttsEngines, translationEngines, loading: enginesLoading, error: enginesError } =
    useAvailableEngines();

  const [state, setState] = useState<FormState>({
    mode: "translate",
    file: null,
    engineName: "",
    params: {},
    jobId: null,
    jobState: "idle",
    errorMessage: null,
    ttsResult: null,
    translationResult: null,
  });

  // Primary language fields
  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguage, setTargetLanguage] = useState("cs");
  const [ttsLanguageCode, setTtsLanguageCode] = useState("cs-CZ");

  const { jobStatus, isPolling, timedOut } = useJobPoller(
    state.jobState === "polling" ? state.jobId : null
  );

  // When polling completes, update state
  if (state.jobState === "polling" && !isPolling && jobStatus) {
    if (jobStatus.status === "COMPLETED") {
      const result = jobStatus.result;
      if (state.mode === "read" && result && "outputFiles" in result) {
        setState((s) => ({ ...s, jobState: "done", ttsResult: result as TTSResultWithFile }));
      } else if (state.mode === "translate" && result && "outputFile" in result) {
        setState((s) => ({
          ...s,
          jobState: "done",
          translationResult: result as TranslationResultWithFile,
        }));
      } else {
        setState((s) => ({ ...s, jobState: "done" }));
      }
    } else if (jobStatus.status === "FAILED") {
      setState((s) => ({
        ...s,
        jobState: "error",
        errorMessage: jobStatus.error ?? "Job failed",
      }));
    }
  }

  if (state.jobState === "polling" && timedOut) {
    setState((s) => ({
      ...s,
      jobState: "error",
      errorMessage: "Job timed out after 10 minutes",
    }));
  }

  const [generateSpeech] = useMutation<{ generateSpeech: TTSResultWithFile | JobCreated }>(GENERATE_SPEECH_MUTATION);
  const [translateText] = useMutation<{ translateText: TranslationResultWithFile | JobCreated }>(TRANSLATE_TEXT_MUTATION);

  const activeEngines: EngineDetail[] = state.mode === "translate" ? translationEngines : ttsEngines;
  const selectedEngine = activeEngines.find((e: EngineDetail) => e.name === state.engineName);

  // Auto-select first engine when engines load or mode changes
  if (!state.engineName && activeEngines.length > 0) {
    const first = activeEngines[0];
    setState((s) => ({
      ...s,
      engineName: first.name,
      params: buildDefaultParams(first),
    }));
  }

  const handleModeChange = (_: React.SyntheticEvent, newMode: Mode) => {
    setState((s) => ({
      ...s,
      mode: newMode,
      engineName: "",
      params: {},
      jobId: null,
      jobState: "idle",
      errorMessage: null,
      ttsResult: null,
      translationResult: null,
      // file is preserved intentionally
    }));
  };

  const handleEngineChange = (engineName: string) => {
    const engine = activeEngines.find((e: EngineDetail) => e.name === engineName);
    setState((s) => ({
      ...s,
      engineName,
      params: engine ? buildDefaultParams(engine) : {},
    }));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".txt") && file.type !== "text/plain") {
      setState((s) => ({
        ...s,
        errorMessage: "Only .txt files are accepted",
      }));
      e.target.value = "";
      return;
    }
    setState((s) => ({ ...s, file, errorMessage: null }));
  };

  const handleParamChange = (field: string, value: unknown) => {
    setState((s) => ({ ...s, params: { ...s.params, [field]: value } }));
  };

  const handleSubmit = async () => {
    if (!state.file) return;

    setState((s) => ({ ...s, jobState: "submitting", errorMessage: null }));

    try {
      const fileContent = await state.file.text();

      if (state.mode === "translate") {
        const input = {
          textContent: fileContent,
          translationEngine: state.engineName,
          sourceLanguage,
          targetLanguage,
          ...state.params,
        };
        const { data } = await translateText({ variables: { input, asyncMode: true } });
        const result = data?.translateText;
        if (result && "jobId" in result) {
          setState((s) => ({
            ...s,
            jobId: (result as JobCreated).jobId,
            jobState: "polling",
          }));
        } else if (result && "outputFile" in result) {
          setState((s) => ({
            ...s,
            jobState: "done",
            translationResult: result as TranslationResultWithFile,
          }));
        }
      } else {
        const input = {
          textContent: fileContent,
          ttsEngine: state.engineName,
          languageCode: ttsLanguageCode,
          ...state.params,
        };
        const { data } = await generateSpeech({ variables: { input, asyncMode: true } });
        const result = data?.generateSpeech;
        if (result && "jobId" in result) {
          setState((s) => ({
            ...s,
            jobId: (result as JobCreated).jobId,
            jobState: "polling",
          }));
        } else if (result && "outputFiles" in result) {
          setState((s) => ({
            ...s,
            jobState: "done",
            ttsResult: result as TTSResultWithFile,
          }));
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      setState((s) => ({ ...s, jobState: "error", errorMessage: msg }));
    }
  };

  const isSubmitting = state.jobState === "submitting" || state.jobState === "polling";
  const canSubmit = !!state.file && !isSubmitting && !enginesError;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        TTS & Translation
      </Typography>

      <Paper sx={{ p: 3 }}>
        {/* Mode tabs */}
        <Tabs value={state.mode} onChange={handleModeChange} sx={{ mb: 3 }}>
          <Tab label="Translate" value="translate" />
          <Tab label="Read (TTS)" value="read" />
        </Tabs>

        {/* Engine loading/error */}
        {enginesLoading && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
            <CircularProgress size={16} />
            <Typography variant="body2">Loading engines…</Typography>
          </Box>
        )}
        {enginesError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load engines: {enginesError.message}
          </Alert>
        )}

        {/* File upload */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Input file (.txt)
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<UploadFileIcon />}
              onClick={() => fileInputRef.current?.click()}
            >
              {state.file ? "Change file" : "Upload .txt file"}
            </Button>
            {state.file && (
              <>
                <Typography variant="body2">
                  {state.file.name} ({(state.file.size / 1024).toFixed(1)} KB)
                </Typography>
                <Button
                  size="small"
                  color="inherit"
                  onClick={() => {
                    setState((s) => ({ ...s, file: null }));
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                >
                  <CloseIcon fontSize="small" />
                </Button>
              </>
            )}
          </Box>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt"
            style={{ display: "none" }}
            onChange={handleFileSelect}
          />
        </Box>

        {/* Primary fields */}
        <Box sx={{ mb: 3 }}>
          {state.mode === "translate" ? (
            <Box sx={{ display: "flex", gap: 2 }}>
              <TextField
                label="Source language"
                size="small"
                value={sourceLanguage}
                onChange={(e) => setSourceLanguage(e.target.value)}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Target language"
                size="small"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                sx={{ flex: 1 }}
              />
            </Box>
          ) : (
            <TextField
              label="Language code"
              size="small"
              value={ttsLanguageCode}
              onChange={(e) => setTtsLanguageCode(e.target.value)}
              fullWidth
              helperText="e.g. cs-CZ, en-US"
            />
          )}
        </Box>

        {/* Engine selector */}
        {activeEngines.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <EngineSelector
              engines={activeEngines}
              value={state.engineName}
              onChange={handleEngineChange}
              disabled={isSubmitting}
            />
          </Box>
        )}

        {/* Dynamic form */}
        {selectedEngine && (
          <Box sx={{ mb: 3 }}>
            <Divider sx={{ mb: 2 }} />
            <DynamicForm
              engineDetail={selectedEngine}
              params={state.params}
              onChange={handleParamChange}
            />
          </Box>
        )}

        {/* Error message */}
        {state.errorMessage && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {state.errorMessage}
          </Alert>
        )}

        {/* Submit */}
        <Button
          variant="contained"
          size="large"
          fullWidth
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          {isSubmitting ? (
            <CircularProgress size={20} color="inherit" />
          ) : state.mode === "translate" ? (
            "Translate"
          ) : (
            "Generate Speech"
          )}
        </Button>

        {/* Progress */}
        {state.jobState === "polling" && jobStatus?.progress && (
          <JobProgress
            percentage={jobStatus.progress.percentage}
            stage={jobStatus.progress.stage}
          />
        )}

        {/* Results */}
        {state.jobState === "done" && (
          <ResultPanel
            mode={state.mode}
            ttsResult={state.ttsResult ?? undefined}
            translationResult={state.translationResult ?? undefined}
          />
        )}
      </Paper>
    </Container>
  );
}
