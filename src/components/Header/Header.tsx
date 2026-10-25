'use client';

/* BUILD TRACE: BT-001
 * PURPOSE: Application Header Shell
 * RESEARCH CONNECTION: Application navigation
 */
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Header() {
  const pathname = usePathname();

  return (
    <header className="header">
      <div className="header-identity">
        <div className="header-subject">
          <Link href="/">
            <img src="/brand-assets/ail-header.png" alt="A Realtime Tech" className="brand-logo" />
          </Link>
        </div>
      </div>

      <div className="header-controls" style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flex: 1 }}>
        <Link href="/walkthrough" className={'btn-header ' + (pathname === '/walkthrough' ? 'active' : '')}>
          WALKTHROUGH
        </Link>
        <Link href="/workflow" className={'btn-header ' + (pathname === '/workflow' ? 'active' : '')}>
          WORKFLOW
        </Link>
      </div>

      <div
        className="header-right"
        style={{ display: 'flex', justifyContent: 'flex-end', flex: 1, paddingRight: '1rem', alignItems: 'center' }}
      >
        <Link href="/start-contributing" className="btn primary">
          Start Contributing
        </Link>
      </div>
    </header>
  );
}
