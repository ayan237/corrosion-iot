import type { Metadata } from "next";
import { Orbitron, JetBrains_Mono, Share_Tech_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const shareTech = Share_Tech_Mono({
  subsets: ["latin"],
  variable: "--font-share-tech",
  display: "swap",
  weight: "400",
});

export const metadata: Metadata = {
  title: "CORROSION INSPECT // Remote AI Terminal",
  description:
    "AI-powered remote corrosion inspection prototype. Not for certified engineering use.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`dark ${orbitron.variable} ${jetbrains.variable} ${shareTech.variable}`}
    >
      <body
        className="min-h-screen antialiased"
        style={{
          fontFamily: "var(--font-jetbrains), var(--font-body)",
          // override CSS vars to use next/font loaded faces
          ["--font-heading" as string]: "var(--font-orbitron), Orbitron, monospace",
          ["--font-body" as string]: "var(--font-jetbrains), JetBrains Mono, monospace",
          ["--font-label" as string]: "var(--font-share-tech), Share Tech Mono, monospace",
        }}
      >
        <Navbar />
        <main className="relative z-[1] max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
