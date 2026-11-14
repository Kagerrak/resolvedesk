import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "ResolveDesk — Support, grounded in knowledge",
  description:
    "A human-reviewed support workspace. Explore an isolated synthetic inbox.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <a href="#main" className="skip">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
