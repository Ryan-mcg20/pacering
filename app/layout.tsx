import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "PacerRing - Heart Rate Monitor",
  description:
    "Premium health dashboard for real-time heart rate monitoring and analysis",
};

export const viewport: Viewport = {
  themeColor: "#000000",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable} style={{ backgroundColor: "#000000" }}>
      <body className="font-sans antialiased min-h-screen text-white" style={{ backgroundColor: "#000000" }}>
        {children}
      </body>
    </html>
  );
}
