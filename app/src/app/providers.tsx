"use client";

import { ApolloProvider } from "@apollo/client/react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { apolloClient } from "@/graphql/client";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1976d2" },
    secondary: { main: "#9c27b0" },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ApolloProvider client={apolloClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ApolloProvider>
  );
}
