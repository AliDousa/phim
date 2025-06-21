import React, { useState, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import SimulationManager from './components/SimulationManager';
import DatasetManager from './components/DatasetManager'; // We'll create this next
import VisualizationDashboard from './components/VisualizationDashboard';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, Beaker, Database, Github } from 'lucide-react';


function App() {
  const [activeView, setActiveView] = useState('dashboard'); // 'dashboard', 'simulations', 'datasets', or 'visualize'
  const [selectedSimId, setSelectedSimId] = useState(null);

  // This would be replaced by a real auth context in a full app
  if (!localStorage.getItem('authToken')) {
    localStorage.setItem('authToken', 'dummy-dev-token');
  }

  // Memoized callback to prevent re-renders
  const handleSelectSimulation = useCallback((simId) => {
    setSelectedSimId(simId);
    setActiveView('visualize');
  }, []);

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard setActiveView={setActiveView} onSelectSimulation={handleSelectSimulation} />;
      case 'simulations':
        return <SimulationManager onSelectSimulation={handleSelectSimulation} />;
      case 'datasets':
        return <DatasetManager />;
      case 'visualize':
        return <VisualizationDashboard simulationId={selectedSimId} />;
      default:
        return <Dashboard setActiveView={setActiveView} onSelectSimulation={handleSelectSimulation} />;
    }
  };

  const NavButton = ({ viewName, icon, children }) => (
    <Button
      variant={activeView.startsWith(viewName) ? 'secondary' : 'ghost'}
      className="w-full justify-start"
      onClick={() => {
        // Reset selected sim ID when navigating away from visualize view
        if (viewName !== 'visualize') setSelectedSimId(null);
        setActiveView(viewName)
      }}
    >
      {icon}
      {children}
    </Button>
  );

  return (
    <div className="flex min-h-screen bg-gray-100/50 dark:bg-gray-900/50">
      <nav className="hidden md:flex flex-col w-64 bg-white dark:bg-gray-950 border-r dark:border-gray-800 p-4 space-y-2">
        <div className="flex items-center space-x-2 mb-6">
          <Beaker className="h-8 w-8 text-primary" />
          <h2 className="text-xl font-bold">PHIM Platform</h2>
        </div>

        <NavButton viewName="dashboard" icon={<LayoutDashboard className="mr-2 h-4 w-4" />}>
          Dashboard
        </NavButton>
        <NavButton viewName="simulations" icon={<Beaker className="mr-2 h-4 w-4" />}>
          Simulations
        </NavButton>
        <NavButton viewName="datasets" icon={<Database className="mr-2 h-4 w-4" />}>
          Datasets
        </NavButton>

        <div className="flex-grow" />
        <div className="text-center text-xs text-gray-500">
          <a href="https://github.com/your-repo" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center hover:text-primary">
            <Github className="mr-2 h-4 w-4" /> View on GitHub
          </a>
          <p className="mt-2">Version 1.1.0</p>
        </div>
      </nav>

      <main className="flex-1 overflow-auto">
        {renderActiveView()}
      </main>
    </div>
  );
}

export default App;