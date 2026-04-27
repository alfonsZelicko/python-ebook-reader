"use client";

import { Box, LinearProgress, Typography } from "@mui/material";

interface JobProgressProps {
  percentage: number;
  stage: string;
}

export function JobProgress({ percentage, stage }: JobProgressProps) {
  const clamped = Math.min(100, Math.max(0, percentage));

  return (
    <Box sx={{ width: "100%", mt: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2" color="text.secondary">
          {stage || "Processing…"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {clamped.toFixed(0)}%
        </Typography>
      </Box>
      <LinearProgress variant="determinate" value={clamped} />
    </Box>
  );
}
