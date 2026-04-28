"use client";

import { Box, Divider, Typography } from "@mui/material";
import { ParameterField } from "./ParameterField";
import type { EngineDetail, ParameterMeta } from "@/types/graphql";

interface DynamicFormProps {
  engineDetail: EngineDetail;
  params: Record<string, unknown>;
  onChange: (field: string, value: unknown) => void;
}

function renderField(
  param: ParameterMeta,
  params: Record<string, unknown>,
  onChange: (field: string, value: unknown) => void
) {
  const value = params[param.name] ?? (param.defaultValue !== undefined
    ? tryParseDefault(param.defaultValue, param.fieldType)
    : "");

  return (
    <ParameterField
      key={param.name}
      name={param.name}
      label={param.label}
      fieldType={param.fieldType}
      choices={param.choices}
      accept={param.accept}
      defaultValue={param.defaultValue}
      value={value}
      helpText={param.helpText}
      required={param.required}
      onChange={(val) => onChange(param.name, val)}
    />
  );
}

function tryParseDefault(defaultValue: string, fieldType: string): unknown {
  try {
    if (fieldType === "boolean") return defaultValue === "true";
    if (fieldType === "number") return Number(defaultValue);
    return defaultValue;
  } catch {
    return defaultValue;
  }
}

export function DynamicForm({ engineDetail, params, onChange }: DynamicFormProps) {
  const { requiredParameters, optionalParameters } = engineDetail;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {requiredParameters.length > 0 && (
        <>
          <Typography variant="subtitle2" color="text.secondary">
            Required parameters
          </Typography>
          {requiredParameters.map((p) => renderField(p, params, onChange))}
        </>
      )}

      {optionalParameters.length > 0 && (
        <>
          {requiredParameters.length > 0 && <Divider />}
          <Typography variant="subtitle2" color="text.secondary">
            Optional parameters
          </Typography>
          {optionalParameters.map((p) => renderField(p, params, onChange))}
        </>
      )}
    </Box>
  );
}
