import "./globals.css";
import ClientLayout from "../components/Layout/ClientLayout";

export const metadata = {
  title: "Telecom Outage Monitor",
  description: "Advanced analytics and recovery tracking for Swedish telecom networks",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}
