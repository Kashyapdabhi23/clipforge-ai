import React, { useEffect, useState } from 'react';
import { 
  FolderKanban, 
  Film, 
  Clock, 
  Calendar, 
  Trash2, 
  ArrowRight, 
  Play, 
  Loader2,
  Plus
} from 'lucide-react';
import { listProjects, deleteProject, resolveMediaUrl } from '../services/api';

export default function MyProjects({ setActiveTab, setSelectedProjectId }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDeleteProject = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project and all its generated clips?')) return;
    try {
      await deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Projects</h2>
          <p className="text-sm text-slate-400 mt-1">
            Access previous video footage batches, inspection history, and generated clip packages.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('create')}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl brand-gradient brand-gradient-hover text-white text-xs font-semibold glow-primary shadow transition cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {loading ? (
        <div className="py-20 flex justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-[#747CFF]" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-20 bg-[#131A2B] border border-dashed border-slate-800 rounded-2xl">
          <FolderKanban className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No projects found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto mb-4">
            Upload footage or ingest an authorized video URL to start your first batch.
          </p>
          <button
            onClick={() => setActiveTab('create')}
            className="px-5 py-2.5 rounded-xl brand-gradient text-white text-xs font-semibold glow-primary cursor-pointer"
          >
            Create New Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => {
                setSelectedProjectId(proj.id);
                setActiveTab('clips');
              }}
              className="group rounded-2xl bg-[#131A2B] border border-slate-800 hover:border-[#747CFF]/50 transition-all duration-300 overflow-hidden flex flex-col justify-between shadow-lg cursor-pointer"
            >
              {/* Thumbnail Container */}
              <div className="aspect-video bg-black relative overflow-hidden">
                {proj.thumbnail_url ? (
                  <img
                    src={resolveMediaUrl(proj.thumbnail_url)}
                    alt={proj.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-slate-900">
                    <Film className="w-10 h-10 text-slate-600" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-[#131A2B] via-transparent to-transparent" />

                {/* Status Badge */}
                <div className="absolute top-3 right-3">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                      proj.status === 'COMPLETED'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                        : proj.status === 'FAILED'
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {proj.status}
                  </span>
                </div>
              </div>

              {/* Info Container */}
              <div className="p-5 space-y-4">
                <div>
                  <h3 className="text-base font-bold text-white group-hover:text-[#9B9EFF] transition line-clamp-1">
                    {proj.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 truncate">
                    {proj.original_filename || proj.source_url || 'Video Footage'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 py-3 border-y border-slate-800/80 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-[#747CFF]" />
                    <span>Duration: <strong className="text-slate-200">{Math.round(proj.duration)}s</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Film className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Clips: <strong className="text-slate-200">{proj.clip_count}</strong></span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => handleDeleteProject(proj.id, e)}
                      className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition"
                      title="Delete Project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>

                    <span className="flex items-center gap-1 text-xs font-semibold text-[#747CFF] group-hover:text-white transition">
                      <span>View Clips</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
