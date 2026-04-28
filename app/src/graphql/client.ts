"use client";

import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client";

/**
 * Creates a new Apollo client instance.
 * Called once per browser session inside ApolloProvider.
 * Using a factory (not a module-level singleton) ensures each SSR request
 * gets a fresh cache, while the browser reuses the same instance.
 */
export function makeApolloClient() {
  return new ApolloClient({
    link: new HttpLink({
      uri: process.env.NEXT_PUBLIC_GRAPHQL_URL ?? "http://localhost:8000/graphql",
    }),
    cache: new InMemoryCache(),
  });
}
