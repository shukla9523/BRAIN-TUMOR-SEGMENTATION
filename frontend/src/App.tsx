import React, { useState, useEffect } from 'react';
import { Navbar } from './components/common/Navbar';
import { Footer } from './components/common/Footer';
import { DisclaimerBanner } from './components/common/DisclaimerBanner';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvaluationPage } from './pages/EvaluationPage';
import { AboutPage } from './pages/AboutPage';
import { HealthResponse, ModelInfoResponse } from './types/mri';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('landing');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [isDark, setIsDark] = useState<boolean>(() => {
    return localStorage.getItem('neuroscan_theme') === 'dark';
  });

  // Apply dark mode class to root HTML element
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('neuroscan_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('neuroscan_theme', 'light');
    }
  }, [isDark]);

  // Initial health check & model info query
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [h, m] = await Promise.all([
          api.getHealth(),
          api.getModelInfo()
        ]);
        setHealth(h);
        setModelInfo(m);
      } catch (err) {
        console.warn('API status polling failed:', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => setIsDark((prev) => !prev);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Top Clinical Disclaimer Alert */}
      <DisclaimerBanner dismissible />

      {/* Main Navbar */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        modelAvailable={health?.model_available ?? false}
        deviceInfo={health?.device ?? 'cpu'}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      {/* Tab Pages Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8">
        {currentTab === 'landing' && (
          <LandingPage
            onStartAnalysis={() => setCurrentTab('workspace')}
            onExploreEvaluation={() => setCurrentTab('evaluation')}
            modelAvailable={health?.model_available ?? false}
          />
        )}

        {currentTab === 'dashboard' && (
          <DashboardPage
            health={health}
            modelInfo={modelInfo}
            onNavigateToWorkspace={() => setCurrentTab('workspace')}
            onNavigateToEvaluation={() => setCurrentTab('evaluation')}
          />
        )}

        {currentTab === 'workspace' && (
          <WorkspacePage
            modelAvailable={health?.model_available ?? false}
          />
        )}

        {currentTab === 'evaluation' && (
          <EvaluationPage />
        )}

        {currentTab === 'methodology' && (
          <AboutPage />
        )}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default App;
