import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import CreateClips from './pages/CreateClips';
import MyProjects from './pages/MyProjects';
import AllClips from './pages/AllClips';
import ProcessingQueue from './pages/ProcessingQueue';
import Settings from './pages/Settings';
import { getHealth } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [recentJobId, setRecentJobId] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const h = await getHealth();
        setHealth(h);
      } catch (e) {
        setHealth({ status: 'offline' });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-[#090D18] text-[#F4F6FF] overflow-hidden select-none">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          health={health} 
        />

        <main className="flex-1 overflow-y-auto p-8">
          {activeTab === 'dashboard' && (
            <Dashboard 
              setActiveTab={setActiveTab} 
              setSelectedProjectId={setSelectedProjectId} 
            />
          )}

          {activeTab === 'create' && (
            <CreateClips 
              setActiveTab={setActiveTab} 
              setRecentJobId={setRecentJobId} 
            />
          )}

          {activeTab === 'projects' && (
            <MyProjects 
              setActiveTab={setActiveTab} 
              setSelectedProjectId={setSelectedProjectId} 
            />
          )}

          {activeTab === 'clips' && (
            <AllClips 
              selectedProjectId={selectedProjectId} 
              setSelectedProjectId={setSelectedProjectId} 
            />
          )}

          {activeTab === 'queue' && (
            <ProcessingQueue 
              setActiveTab={setActiveTab} 
              recentJobId={recentJobId} 
              setSelectedProjectId={setSelectedProjectId} 
            />
          )}

          {activeTab === 'settings' && (
            <Settings />
          )}
        </main>
      </div>
    </div>
  );
}
