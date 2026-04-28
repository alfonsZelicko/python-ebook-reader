"use client";

import {
  Alert,
  Button,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import type { TTSResultWithFile, TranslationResultWithFile } from "@/types/graphql";

type Mode = "translate" | "read";

interface ResultPanelProps {
  mode: Mode;
  ttsResult?: TTSResultWithFile;
  translationResult?: TranslationResultWithFile;
}

export function ResultPanel({ mode, ttsResult, translationResult }: ResultPanelProps) {
  if (mode === "read" && ttsResult) {
    const dl = ttsResult.fileDownload;
    return (
      <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          TTS Result
        </Typography>

        {dl?.downloadUrl && (
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            href={dl.downloadUrl}
            download={dl.filename}
            sx={{ mb: 2 }}
          >
            Download {dl.filename}
          </Button>
        )}

        {!dl?.downloadUrl && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Generated {ttsResult.outputFiles.length} audio file(s)
          </Alert>
        )}

        <Divider sx={{ my: 1 }} />
        <Typography variant="subtitle2" gutterBottom>
          Metadata
        </Typography>
        <Table size="small">
          <TableBody>
            <TableRow>
              <TableCell>Engine</TableCell>
              <TableCell>{ttsResult.metadata.engineUsed}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Duration</TableCell>
              <TableCell>{ttsResult.metadata.totalDurationSeconds}s</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Chunks</TableCell>
              <TableCell>{ttsResult.metadata.totalChunks}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Paper>
    );
  }

  if (mode === "translate" && translationResult) {
    return (
      <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Translation Result
        </Typography>

        {translationResult.fileDownload?.downloadUrl ? (
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            href={translationResult.fileDownload.downloadUrl}
            download={translationResult.fileDownload.filename}
            sx={{ mb: 2 }}
          >
            Download {translationResult.fileDownload.filename}
          </Button>
        ) : (
          <Alert severity="info" sx={{ mb: 2 }}>
            Output file: {translationResult.outputFile}
          </Alert>
        )}

        <Divider sx={{ my: 1 }} />
        <Typography variant="subtitle2" gutterBottom>
          Metadata
        </Typography>
        <Table size="small">
          <TableBody>
            <TableRow>
              <TableCell>Engine</TableCell>
              <TableCell>{translationResult.metadata.engineUsed}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Source language</TableCell>
              <TableCell>{translationResult.metadata.sourceLanguage}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Target language</TableCell>
              <TableCell>{translationResult.metadata.targetLanguage}</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Chunks</TableCell>
              <TableCell>{translationResult.metadata.totalChunks}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Paper>
    );
  }

  return null;
}
