"use client";

import { useRef } from "react";
import {
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { HelpIcon } from "./HelpIcon";
import type { FieldType } from "@/types/graphql";

export interface ParameterFieldProps {
  name: string;
  label: string;
  fieldType: FieldType;
  choices?: string[];
  accept?: string;
  defaultValue?: string;
  value: unknown;
  helpText?: string;
  required: boolean;
  onChange: (value: unknown) => void;
}

export function ParameterField({
  name,
  label,
  fieldType,
  choices,
  accept,
  value,
  helpText,
  required,
  onChange,
}: ParameterFieldProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const labelWithRequired = required ? `${label} *` : label;

  const LabelRow = (
    <Box sx={{ display: "flex", alignItems: "center", mb: 0.5 }}>
      <Typography variant="body2" component="label" htmlFor={name}>
        {labelWithRequired}
      </Typography>
      <HelpIcon helpText={helpText} />
    </Box>
  );

  // Select (enum/choices)
  if (fieldType === "select" && choices && choices.length > 0) {
    return (
      <FormControl fullWidth size="small">
        <InputLabel id={`${name}-label`}>{labelWithRequired}</InputLabel>
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <Select
            labelId={`${name}-label`}
            id={name}
            value={String(value ?? choices[0])}
            label={labelWithRequired}
            onChange={(e) => onChange(e.target.value)}
            sx={{ flex: 1 }}
          >
            {choices.map((c) => (
              <MenuItem key={c} value={c}>
                {c}
              </MenuItem>
            ))}
          </Select>
          <HelpIcon helpText={helpText} />
        </Box>
      </FormControl>
    );
  }

  // Boolean (checkbox)
  if (fieldType === "boolean") {
    return (
      <Box sx={{ display: "flex", alignItems: "center" }}>
        <FormControlLabel
          control={
            <Checkbox
              id={name}
              checked={Boolean(value)}
              onChange={(e) => onChange(e.target.checked)}
              size="small"
            />
          }
          label={labelWithRequired}
        />
        <HelpIcon helpText={helpText} />
      </Box>
    );
  }

  // File upload
  if (fieldType === "file") {
    const selectedFile = value instanceof File ? value : null;
    return (
      <Box>
        {LabelRow}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => fileInputRef.current?.click()}
          >
            {selectedFile ? selectedFile.name : "Choose file…"}
          </Button>
          {selectedFile && (
            <Typography variant="caption" color="text.secondary">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </Typography>
          )}
          <input
            ref={fileInputRef}
            id={name}
            type="file"
            accept={accept}
            style={{ display: "none" }}
            onChange={(e) => onChange(e.target.files?.[0] ?? null)}
          />
        </Box>
      </Box>
    );
  }

  // Number
  if (fieldType === "number") {
    return (
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        <TextField
          id={name}
          label={labelWithRequired}
          type="number"
          size="small"
          fullWidth
          value={value ?? ""}
          onChange={(e) =>
            onChange(e.target.value === "" ? "" : Number(e.target.value))
          }
        />
        <HelpIcon helpText={helpText} />
      </Box>
    );
  }

  // Default: text
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <TextField
        id={name}
        label={labelWithRequired}
        type="text"
        size="small"
        fullWidth
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
      />
      <HelpIcon helpText={helpText} />
    </Box>
  );
}
