import React from 'react';
import { AppProvider, useAppContext } from './context/AppContext';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import KYC from './pages/KYC';
import Selection from './pages/Selection';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import Result from './pages/Result';
import Config from './pages/Config';
import Preliminary from './pages/Preliminary';
import Partners from './pages/Partners';
import About from './pages/About';
import HowItWorks from './pages/HowItWorks';

const NavigationSource = () => {
  const { view } = useAppContext();

  switch (view) {
    case 'landing': return <Landing />;
    case 'kyc': return <KYC />;
    case 'selection': return <Selection />;
    case 'prelim': return <Preliminary />;
    case 'upload': return <Upload />;
    case 'analysis': return <Analysis />;
    case 'result': return <Result />;
    case 'config': return <Config />;
    case 'partner': return <Partners />;
    case 'about': return <About />;
    case 'how': return <HowItWorks />;
    default: return <Landing />;
  }
};

const AppShell = () => {
  const { view } = useAppContext();
  const scrollViews = new Set(['config', 'upload', 'prelim', 'kyc', 'partner', 'about', 'how', 'result']);
  const allowScroll = scrollViews.has(view);

  return (
    <div className="h-screen bg-[#FAF9F6] flex flex-col overflow-hidden">
      <Navbar />
      <main className={`flex-1 min-h-0 ${allowScroll ? 'overflow-y-auto' : 'overflow-hidden'}`}>
        <NavigationSource />
      </main>
    </div>
  );
};

function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}

export default App;
