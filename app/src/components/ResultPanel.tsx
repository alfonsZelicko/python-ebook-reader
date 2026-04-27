"use client";

import {
  Alert,
  Box,
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
    return (
      <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          TTS Result
        </Typography>

        {ttsResult.outputFiles.map((file, i) => (
          <Box key={file} sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              File {i + 1}: {file}
            </Typography>
            {ttsResult.fileDownload?.downloadUrl && (
              <>
                {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
                <audio
                  controls
                  src={ttsResult.fileDownload.downloadUrl}
                  style={{ width: "100%", marginBottom: 8 }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<DownloadIcon />}
                  href={ttsResult.fileDownload.downloadUrl}
                  download={ttsResult.fileDownload.filename}
                >
                  Download
                </Button>
              </>
            )}
          </Box>
        ))}

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
