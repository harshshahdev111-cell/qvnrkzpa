import React from 'react';
import { Activity, Info, Wind } from 'lucide-react';

export function AppLayout({ activePage, onNavigate, children }) {
  return (
    <div className="shell">
      <aside>
        <a className="brand" href="/">
          <span className="logo">
            <Wind size={23} />
          </span>
          wind<span className="light">desk</span>
          <span className="brand-dot">.</span>
        </a>
        <div className="workspace">WORKSPACE</div>
        <button
          className={activePage === 'overview' ? 'nav active' : 'nav'}
          onClick={() => onNavigate('overview')}
        >
          <Activity size={18} /> Decision overview
        </button>
        <button
          className={activePage === 'method' ? 'nav active' : 'nav'}
          onClick={() => onNavigate('method')}
        >
          <Info size={18} /> Methodology
        </button>
        <div className="aside-bottom">
          <span className="green-dot" /> Elexon Insights
          <div>Great Britain · National wind</div>
          <small>January 2026 pilot</small>
        </div>
      </aside>
      <main>
        <header>
          <div className="crumb">
            Trading intelligence <span>/</span> Day-ahead wind
          </div>
          <div className="pilot">
            PILOT WORKSPACE <span>GB</span>
          </div>
        </header>
        <section className="content">{children}</section>
      </main>
    </div>
  );
}
