import React from 'react';
import { 
  LayoutDashboard, 
  Sparkles, 
  FolderKanban, 
  Film, 
  ListOrdered, 
  Settings, 
  Cpu, 
  Scissors
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'create', label: 'Create Clips', icon: Sparkles, badge: 'AI' },
    { id: 'projects', label: 'My Projects', icon: FolderKanban },
    { id: 'clips', label: 'All Clips', icon: Film },
    { id: 'queue', label: 'Processing Queue', icon: ListOrdered },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#131A2B] border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-6 flex items-center gap-3 border-b border-slate-800/80">
          <div className="w-10 h-10 rounded-xl brand-gradient flex items-center justify-center glow-primary">
            <Scissors className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-[#9B9EFF] bg-clip-text text-transparent">
              ClipForge <span className="text-[#747CFF]">AI</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">Smart Viral Video Engine</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl font-medium text-sm transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'bg-[#747CFF] text-white shadow-lg shadow-[#747CFF]/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'bg-[#747CFF]/20 text-[#9B9EFF]'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Hardware / Performance Footer Badge */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-1.5">
          <Cpu className="w-4 h-4 text-[#747CFF]" />
          <span className="text-xs font-semibold text-slate-300">Lightweight Mode</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Whisper INT8 • Ultrafast CPU • 8 GB RAM Optimized
        </p>
        <div className="mt-2.5 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-[10px] text-emerald-400 font-medium">System Ready</span>
        </div>
      </div>
    </aside>
  );
}
