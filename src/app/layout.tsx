import type { Metadata } from 'next';
import '../index.css';
import '../App.css';
import { Header } from '../components/Header/Header';

export const metadata: Metadata = {
  title: 'ART Investigation Lab',
  description: 'Turn discoveries into shared intelligence.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          <Header />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
