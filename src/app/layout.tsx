import type { Metadata } from 'next';
import '../index.css';
import '../App.css';

export const metadata: Metadata = {
  title: 'ERPNext Supplier Delivery & Delay Control Center',
  description: 'Supplier Delivery Confirmation & Delay Escalation for ERPNext',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
