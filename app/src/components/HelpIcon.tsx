"use client";

import { Tooltip, IconButton } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

interface HelpIconProps {
  helpText?: string;
}

export function HelpIcon({ helpText }: HelpIconProps) {
  if (!helpText) return null;

  return (
    <Tooltip title={helpText} arrow placement="top">
      <IconButton size="small" sx={{ ml: 0.5, p: 0.25, color: "text.secondary" }}>
        <InfoOutlinedIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );
}
