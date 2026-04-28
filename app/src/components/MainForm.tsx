"use client";

import { useRef, useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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
  file: File | null;
  engineName: string;
  params: Record<string, unknown>;
  jobState: JobState;
  errorMessage: string | null;
  ttsResult: TTSResultWithFile | null;
  translationResult: TranslationResultWithFile | null;
}

interface MainFormProps {
  mode: Mode;
}

// Isolated so useSearchParams() lives inside its own Suspense boundary —
// prevents hydration mismatch from wrapping the whole page in Suspense.
function SearchParamsReader({ onJobId }: { onJobId: (id: string | null) => void }) {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  useEffect(() => { onJobId(jobId); }, [jobId, onJobId]);
  return null;
}

function buildDefaultParams(engine: EngineDetail): Record<string, unknown> {
  const defaults: Record<string, unknown> = {};
  const allParams: ParameterMeta[] = [
    ...engine.requiredParameters,
    ...engine.optionalParameters,
  ];
  for (const p of allParams) {
    if (p.fieldType === "boolean") {
      defaults[p.name] = p.defaultValue !== undefined ? p.defaultValue === "true" : false;
    } else if (p.defaultValue !== undefined) {
      try {
        if (p.fieldType === "number") defaults[p.name] = Number(p.defaultValue);
        else defaults[p.name] = p.defaultValue;
      } catch {
        defaults[p.name] = p.defaultValue;
      }
    }
  }
  return defaults;
}

export function MainForm({ mode }: MainFormProps) {
  const router = useRouter();
  const [jobIdFromUrl, setJobIdFromUrl] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { ttsEngines, translationEngines, loading: enginesLoading, error: enginesError } =
    useAvailableEngines();

  const [state, setState] = useState<FormState>({
    file: null,
    engineName: "",
    params: {},
    jobState: "idle",
    errorMessage: null,
    ttsResult: null,
    translationResult: null,
  });

  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguage, setTargetLanguage] = useState("cs");
  const [ttsLanguageCode, setTtsLanguageCode] = useState("cs-CZ");

  // When jobId appears in URL (e.g. page load/refresh with ?jobId=...), start polling
  useEffect(() => {
    if (jobIdFromUrl && state.jobState === "idle") {
      setState((s) => ({ ...s, jobState: "polling" }));
    }
  }, [jobIdFromUrl, state.jobState]);

  // jobId lives in URL; derive it from there
  const jobId = jobIdFromUrl;

  const { jobStatus, isPolling, timedOut } = useJobPoller(
    state.jobState === "polling" ? jobId : null
  );

  // Sync polling completion back to state
  useEffect(() => {
    if (state.jobState !== "polling" || isPolling) return;
    if (!jobStatus) return;

    if (jobStatus.status === "COMPLETED") {
      const result = jobStatus.result;
      if (mode === "read" && result && "outputFiles" in result) {
        setState((s) => ({ ...s, jobState: "done", ttsResult: result as TTSResultWithFile }));
      } else if (mode === "translate" && result && "outputFile" in result) {
        setState((s) => ({ ...s, jobState: "done", translationResult: result as TranslationResultWithFile }));
      } else {
        setState((s) => ({ ...s, jobState: "done" }));
      }
    } else if (jobStatus.status === "FAILED") {
      setState((s) => ({
        ...s,
        jobState: "error",
        errorMessage: jobStatus.error ?? "Job failed",
      }));
      // Remove jobId from URL on failure
      router.replace(`/${mode}`);
    }
  }, [state.jobState, isPolling, jobStatus, mode, router]);

  useEffect(() => {
    if (state.jobState === "polling" && timedOut) {
      setState((s) => ({ ...s, jobState: "error", errorMessage: "Job timed out after 10 minutes" }));
      router.replace(`/${mode}`);
    }
  }, [timedOut, state.jobState, mode, router]);

  const [generateSpeech] = useMutation<{ generateSpeech: TTSResultWithFile | JobCreated }>(GENERATE_SPEECH_MUTATION);
  const [translateText] = useMutation<{ translateText: TranslationResultWithFile | JobCreated }>(TRANSLATE_TEXT_MUTATION);

  const activeEngines: EngineDetail[] = mode === "translate" ? translationEngines : ttsEngines;
  const selectedEngine = activeEngines.find((e: EngineDetail) => e.name === state.engineName);

  // Auto-select first engine
  useEffect(() => {
    if (!state.engineName && activeEngines.length > 0) {
      const first = activeEngines[0];
      setState((s) => ({ ...s, engineName: first.name, params: buildDefaultParams(first) }));
    }
  }, [activeEngines, state.engineName]);

  const handleModeChange = (_: React.SyntheticEvent, newMode: Mode) => {
    router.push(`/${newMode}`);
  };

  const handleEngineChange = (engineName: string) => {
    const engine = activeEngines.find((e: EngineDetail) => e.name === engineName);
    setState((s) => ({ ...s, engineName, params: engine ? buildDefaultParams(engine) : {} }));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".txt") && file.type !== "text/plain") {
      setState((s) => ({ ...s, errorMessage: "Only .txt files are accepted" }));
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

      if (mode === "translate") {
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
          const newJobId = (result as JobCreated).jobId;
          setState((s) => ({ ...s, jobState: "polling" }));
          router.replace(`/translate?jobId=${newJobId}`);
        } else if (result && "outputFile" in result) {
          setState((s) => ({ ...s, jobState: "done", translationResult: result as TranslationResultWithFile }));
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
          const newJobId = (result as JobCreated).jobId;
          setState((s) => ({ ...s, jobState: "polling" }));
          router.replace(`/read?jobId=${newJobId}`);
        } else if (result && "outputFiles" in result) {
          setState((s) => ({ ...s, jobState: "done", ttsResult: result as TTSResultWithFile }));
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
      {/* Read jobId from URL inside its own Suspense — avoids hydration mismatch */}
      <Suspense fallback={null}>
        <SearchParamsReader onJobId={setJobIdFromUrl} />
      </Suspense>

      <Typography variant="h4" gutterBottom>
        TTS & Translation
      </Typography>

      <Paper sx={{ p: 3 }}>
        {/* Mode tabs */}
        <Tabs value={mode} onChange={handleModeChange} sx={{ mb: 3 }}>
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
          {mode === "translate" ? (
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
          ) : mode === "translate" ? (
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
            mode={mode}
            ttsResult={state.ttsResult ?? undefined}
            translationResult={state.translationResult ?? undefined}
          />
        )}
      </Paper>
    </Container>
  );
}
