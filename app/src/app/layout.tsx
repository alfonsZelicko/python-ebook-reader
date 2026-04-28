import type { Metadata } from "next";
import { Providers } from "./providers";
import { EmotionCacheProvider } from "./emotion-cache";
import { fetchAvailableEngines } from "@/graphql/apollo-server";
import "./globals.css";

export const metadata: Metadata = {
  title: "TTS & Translation",
  description: "Text-to-Speech and Translation UI",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const initialEngines = await fetchAvailableEngines();

  return (
    <html lang="en">
      <body>
        <EmotionCacheProvider>
          <Providers initialEngines={initialEngines}>
            {children}
          </Providers>
        </EmotionCacheProvider>
      </body>
    </html>
  );
}
