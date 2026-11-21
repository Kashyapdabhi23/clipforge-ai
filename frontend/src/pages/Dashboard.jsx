import React, { useEffect, useState } from 'react';
import { 
  FolderKanban, 
  Film, 
  Loader2, 
  CheckCircle2, 
  HardDrive, 
  Sparkles, 
  ArrowRight,
  Clock,
  Play
} from 'lucide-react';
import { getStats } from '../services/api';

export default function Dashboard({ setActiveTab, setSelectedProjectId }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    {
      title: 'Total Projects',
      value: stats?.total_projects || 0,
      icon: FolderKanban,
      color: 'text-[#747CFF]',
      bg: 'bg-[#747CFF]/10',
      border: 'border-[#747CFF]/20',
    },
    {
      title: 'Clips Generated',
      value: stats?.total_clips || 0,
      icon: Film,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
    },
    {
      title: 'Processing Jobs',
      value: stats?.processing_jobs || 0,
      icon: Loader2,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      spin: (stats?.processing_jobs || 0) > 0,
    },
    {
      title: 'Completed Jobs',
      value: stats?.completed_jobs || 0,
      icon: CheckCircle2,
      color: 'text-[#9B9EFF]',
      bg: 'bg-[#9B9EFF]/10',
      border: 'border-[#9B9EFF]/20',
    },
    {
      title: 'Storage Used',
      value: `${stats?.storage_used_mb || 0} MB`,
      icon: HardDrive,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <div className="relative rounded-2xl overflow-hidden p-8 bg-gradient-to-r from-[#131A2B] via-[#1a233a] to-[#131A2B] border border-slate-800 glow-card">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#747CFF]/15 border border-[#747CFF]/30 text-xs font-semibold text-[#9B9EFF] mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Automated Video Repurposing</span>
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight leading-tight">
            Turn Long Videos Into <span className="text-[#747CFF]">Viral 9:16 Shorts</span> in Minutes
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            Upload your footage or paste a video link. ClipForge AI uses Whisper transcription, scene detection, and multi-factor highlight scoring to craft multiple engaging short videos with synchronized captions.
          </p>
          <div className="mt-6 flex items-center gap-4">
            <button
              onClick={() => setActiveTab('create')}
              className="flex items-center gap-2.5 px-6 py-3 rounded-xl brand-gradient brand-gradient-hover text-white font-semibold text-sm glow-primary transition cursor-pointer shadow-lg"
            >
              <Sparkles className="w-4 h-4" />
              <span>Create New AI Clips</span>
            </button>
            <button
              onClick={() => setActiveTab('clips')}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 font-medium text-sm border border-slate-700 transition cursor-pointer"
            >
              <span>View All Clips</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className={`p-5 rounded-2xl bg-[#131A2B] border ${card.border} transition-all duration-200 hover:border-opacity-60 shadow-md`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">{card.title}</span>
                <div className={`p-2 rounded-xl ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color} ${card.spin ? 'animate-spin' : ''}`} />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {loading ? '...' : card.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Projects Section */}
      <div className="rounded-2xl bg-[#131A2B] border border-slate-800 p-6 shadow-md">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-bold text-white">Recent Projects</h3>
            <p className="text-xs text-slate-400">Recently uploaded footage and generated batches</p>
          </div>
          <button
            onClick={() => setActiveTab('projects')}
            className="text-xs font-semibold text-[#9B9EFF] hover:text-white flex items-center gap-1 transition cursor-pointer"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center text-slate-400 text-sm">
            <Loader2 className="w-6 h-6 animate-spin text-[#747CFF]" />
          </div>
        ) : !stats?.recent_projects?.length ? (
          <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
            <Film className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-400">No video projects created yet.</p>
            <button
              onClick={() => setActiveTab('create')}
              className="mt-3 px-4 py-2 text-xs font-semibold rounded-lg bg-[#747CFF]/20 text-[#9B9EFF] hover:bg-[#747CFF]/30 transition cursor-pointer"
            >
              Create your first project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.recent_projects.map((proj) => (
              <div
                key={proj.id}
                onClick={() => {
                  setSelectedProjectId(proj.id);
                  setActiveTab('clips');
                }}
                className="group p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-[#747CFF]/40 transition-all duration-200 cursor-pointer flex flex-col justify-between"
              >
                <div className="flex items-start gap-3">
                  <div className="w-16 h-20 rounded-lg bg-black shrink-0 overflow-hidden relative border border-slate-800">
                    {proj.thumbnail_url ? (
                      <img
                        src={proj.thumbnail_url}
                        alt={proj.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Play className="w-4 h-4 text-slate-600" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-white truncate group-hover:text-[#9B9EFF] transition">
                      {proj.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {Math.round(proj.duration)}s
                      </span>
                      <span>•</span>
                      <span className="px-1.5 py-0.5 rounded bg-[#747CFF]/15 text-[#9B9EFF] font-semibold text-[11px]">
                        {proj.clip_count} {proj.clip_count === 1 ? 'clip' : 'clips'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span className={`font-medium ${proj.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {proj.status}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {new Date(proj.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
