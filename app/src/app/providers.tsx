"use client";

import { useRef } from "react";
import { ApolloProvider } from "@apollo/client/react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { makeApolloClient } from "@/graphql/client";
import { AVAILABLE_ENGINES_QUERY } from "@/graphql/queries";
import type { EngineInfo } from "@/types/graphql";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1976d2" },
    secondary: { main: "#9c27b0" },
  },
});

interface ProvidersProps {
  children: React.ReactNode;
  initialEngines?: EngineInfo | null;
}

export function Providers({ children, initialEngines }: ProvidersProps) {
  // Stable client instance across re-renders — created once per browser session
  const clientRef = useRef(makeApolloClient());

  // Hydrate Apollo cache with SSR data so the first client render
  // doesn't trigger a redundant network request
  if (initialEngines) {
    try {
      clientRef.current.cache.writeQuery({
        query: AVAILABLE_ENGINES_QUERY,
        data: { availableEngines: initialEngines },
      });
    } catch {
      // Cache write can fail if query shape mismatches — safe to ignore,
      // the client will fetch fresh data on its own
    }
  }

  return (
    <ApolloProvider client={clientRef.current}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ApolloProvider>
  );
}
