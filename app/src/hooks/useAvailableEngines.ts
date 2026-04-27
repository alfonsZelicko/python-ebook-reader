"use client";

import { useQuery } from "@apollo/client/react";
import { AVAILABLE_ENGINES_QUERY } from "@/graphql/queries";
import type { EngineDetail } from "@/types/graphql";

interface AvailableEnginesData {
  availableEngines: {
    ttsEngines: EngineDetail[];
    translationEngines: EngineDetail[];
  };
}

export function useAvailableEngines() {
  const { data, loading, error } = useQuery<AvailableEnginesData>(
    AVAILABLE_ENGINES_QUERY
  );

  return {
    ttsEngines: data?.availableEngines.ttsEngines ?? [],
    translationEngines: data?.availableEngines.translationEngines ?? [],
    loading,
    error,
  };
}
