"use client";

import {
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
} from "@mui/material";
import type { EngineDetail } from "@/types/graphql";

interface EngineSelectorProps {
  engines: EngineDetail[];
  value: string;
  onChange: (engineName: string) => void;
  disabled?: boolean;
}

export function EngineSelector({
  engines,
  value,
  onChange,
  disabled,
}: EngineSelectorProps) {
  const selected = engines.find((e) => e.name === value);

  return (
    <FormControl fullWidth size="small" disabled={disabled}>
      <InputLabel id="engine-selector-label">Engine</InputLabel>
      <Select
        labelId="engine-selector-label"
        id="engine-selector"
        value={value}
        label="Engine"
        onChange={(e) => onChange(e.target.value)}
      >
        {engines.map((engine) => (
          <MenuItem key={engine.name} value={engine.name}>
            {engine.name}
          </MenuItem>
        ))}
      </Select>
      {selected?.description && (
        <FormHelperText>{selected.description}</FormHelperText>
      )}
    </FormControl>
  );
}
