import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Price Predictor",
  description: "Vercel frontend for the stock price prediction API.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
