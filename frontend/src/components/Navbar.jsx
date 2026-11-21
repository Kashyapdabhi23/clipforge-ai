import React from 'react';
import { Sparkles, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health }) {
  const titles = {
    dashboard: 'Dashboard Overview',
    create: 'Create AI Highlights',
    projects: 'Project Management',
    clips: 'Generated Clips Library',
    queue: 'Processing Queue & Status',
    settings: 'System & Engine Settings',
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#090D18]/90 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-lg font-semibold text-white tracking-wide">
          {titles[activeTab] || 'ClipForge AI'}
        </h2>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend health status badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#131A2B] border border-slate-800 text-xs">
          <Activity className={`w-3.5 h-3.5 ${health?.status === 'online' ? 'text-emerald-400' : 'text-amber-400 animate-pulse'}`} />
          <span className="text-slate-300 font-medium">
            Backend: <span className={health?.status === 'online' ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
              {health?.status === 'online' ? 'Online' : 'Checking...'}
            </span>
          </span>
        </div>

        {/* Quick action button */}
        {activeTab !== 'create' && (
          <button
            onClick={() => setActiveTab('create')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl brand-gradient brand-gradient-hover text-white text-xs font-semibold glow-primary transition-all duration-200 cursor-pointer shadow-md"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New AI Clips</span>
          </button>
        )}
      </div>
    </header>
  );
}
