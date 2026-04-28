"use client";

/**
 * Emotion SSR cache for Next.js App Router.
 *
 * Next.js App Router renders Server Components on the server and hydrates
 * them on the client. Emotion generates CSS class names dynamically — without
 * this provider the server and client produce different insertion order/content,
 * causing hydration mismatches.
 *
 * This component uses `useServerInsertedHTML` to flush Emotion styles into the
 * server-rendered HTML, so the client hydrates against identical markup.
 */

import { useRef } from "react";
import { useServerInsertedHTML } from "next/navigation";
import createCache from "@emotion/cache";
import { CacheProvider } from "@emotion/react";

export function EmotionCacheProvider({ children }: { children: React.ReactNode }) {
  const cacheRef = useRef<ReturnType<typeof createCache> | null>(null);

  if (!cacheRef.current) {
    cacheRef.current = createCache({ key: "mui", prepend: true });
    // Disable automatic insertion — we flush manually via useServerInsertedHTML
    cacheRef.current.compat = true;
  }

  useServerInsertedHTML(() => {
    const cache = cacheRef.current!;
    const names = Object.keys(cache.inserted);
    if (!names.length) return null;

    let styles = "";
    for (const name of names) {
      const style = cache.inserted[name];
      if (typeof style === "string") styles += style;
    }

    // Reset so we don't re-insert on subsequent flushes
    cache.inserted = {};

    return (
      <style
        key="emotion-ssr"
        data-emotion={`${cache.key} ${names.join(" ")}`}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    );
  });

  return <CacheProvider value={cacheRef.current}>{children}</CacheProvider>;
}
