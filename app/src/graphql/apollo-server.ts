/**
 * Server-side GraphQL fetch utility.
 * Used in Server Components to fetch data without an Apollo client instance.
 * Results are passed as props and used to hydrate the Apollo cache on the client.
 */

import type { EngineInfo } from "@/types/graphql";

const GRAPHQL_URL =
  process.env.NEXT_PUBLIC_GRAPHQL_URL ?? "http://localhost:8000/graphql";

const AVAILABLE_ENGINES_QUERY = `
  query AvailableEngines {
    availableEngines {
      ttsEngines {
        name
        description
        requiredParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
        optionalParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
      }
      translationEngines {
        name
        description
        requiredParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
        optionalParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
      }
    }
  }
`;

export async function fetchAvailableEngines(): Promise<EngineInfo | null> {
  try {
    const res = await fetch(GRAPHQL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: AVAILABLE_ENGINES_QUERY }),
      // Next.js cache: revalidate every 60s — engines rarely change
      next: { revalidate: 60 },
    });

    if (!res.ok) return null;

    const json = await res.json();
    return (json.data?.availableEngines as EngineInfo) ?? null;
  } catch {
    return null;
  }
}
