import React, { useState } from 'react';
import { AppLayout } from '../components/layout/AppLayout';
import { DecisionPage } from '../features/decisions/DecisionPage';

export default function App() {
  const [activePage, setActivePage] = useState('overview');

  return (
    <AppLayout activePage={activePage} onNavigate={setActivePage}>
      <DecisionPage
        activePage={activePage}
        onMethodology={() => setActivePage('method')}
      />
    </AppLayout>
  );
}
