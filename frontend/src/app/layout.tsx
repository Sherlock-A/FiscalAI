import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FiscalAI — Intelligence Fiscale Municipale",
  description: "Détecte automatiquement les anomalies fiscales dans les communes marocaines. 488 écarts · 1.45M MAD/an récupérables · Aide à la décision.",
  openGraph: {
    title: "FiscalAI — Intelligence Fiscale pour les Communes Marocaines",
    description: "Croise OSM + registre fiscal + connexions ONEE pour surfacer les propriétés non déclarées. Prototype actif sur la commune de Salé.",
    siteName: "FiscalAI",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "FiscalAI dashboard" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "FiscalAI — Intelligence Fiscale Municipale",
    description: "488 anomalies détectées · 1.45M MAD/an récupérables · Commune de Salé",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
