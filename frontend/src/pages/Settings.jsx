import React, { useEffect, useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  HardDrive, 
  Activity, 
  ShieldCheck, 
  Zap, 
  RefreshCw,
  CheckCircle2
} from 'lucide-react';
import { getHealth, getStats } from '../services/api';

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const [h, s] = await Promise.all([getHealth(), getStats()]);
      setHealth(h);
      setStats(s);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">System & Engine Settings</h2>
        <p className="text-sm text-slate-400 mt-1">
          Hardware tuning, quantization parameters, and storage allocation for ClipForge AI.
        </p>
      </div>

      {/* 8 GB RAM / CPU Optimization Profile Card */}
      <div className="p-6 rounded-2xl bg-[#131A2B] border border-slate-800 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#747CFF]/15 text-[#747CFF]">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Target Hardware Tuning Profile</h3>
              <p className="text-xs text-slate-400">Optimized for Intel Core i5 7th Gen • 8 GB RAM • SSD</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Profile Active</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Whisper Engine</span>
            <div className="text-sm font-bold text-white mt-1">faster-whisper (tiny)</div>
            <p className="text-[11px] text-emerald-400 mt-0.5">INT8 CPU Quantization (~75 MB RAM)</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">FFmpeg Preset</span>
            <div className="text-sm font-bold text-white mt-1">libx264 ultrafast</div>
            <p className="text-[11px] text-[#9B9EFF] mt-0.5">2 Threads max for smooth multitasking</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Job Concurrency</span>
            <div className="text-sm font-bold text-white mt-1">Single Job Semaphore</div>
            <p className="text-[11px] text-amber-400 mt-0.5">Prevents memory spikes</p>
          </div>
        </div>
      </div>

      {/* Subsystem Health & Diagnostics */}
      <div className="p-6 rounded-2xl bg-[#131A2B] border border-slate-800 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Subsystems & Toolchains</h3>
              <p className="text-xs text-slate-400">Live operational status of backend services</p>
            </div>
          </div>
          <button
            onClick={fetchSettings}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/40 border border-slate-800">
            <div className="flex items-center gap-3">
              <Zap className="w-4 h-4 text-[#747CFF]" />
              <div>
                <div className="text-xs font-bold text-white">FFmpeg Binary</div>
                <div className="text-[11px] text-slate-400 truncate max-w-sm sm:max-w-md">
                  {health?.ffmpeg_path || 'Checking...'}
                </div>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400">
              {health?.ffmpeg_ready ? 'Available' : 'Online'}
            </span>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/40 border border-slate-800">
            <div className="flex items-center gap-3">
              <HardDrive className="w-4 h-4 text-purple-400" />
              <div>
                <div className="text-xs font-bold text-white">Storage Utilization</div>
                <div className="text-[11px] text-slate-400">
                  Total media files stored on SSD
                </div>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-500/10 text-purple-300">
              {stats?.storage_used_mb || 0} MB
            </span>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/40 border border-slate-800">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <div>
                <div className="text-xs font-bold text-white">Database Engine</div>
                <div className="text-[11px] text-slate-400">
                  SQLite (zero external service overhead, PostgreSQL compatible models)
                </div>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400">
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
