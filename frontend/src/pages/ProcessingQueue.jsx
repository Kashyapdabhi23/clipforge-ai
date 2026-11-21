import React, { useEffect, useState } from 'react';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ArrowRight, 
  Film, 
  Sparkles,
  Download,
  ListOrdered
} from 'lucide-react';
import { listJobs, getJobDetails, getZipDownloadUrl } from '../services/api';

export default function ProcessingQueue({ setActiveTab, recentJobId, setSelectedProjectId }) {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(true);

  const stepsPipeline = [
    { key: 'queued', label: 'Queued in Engine' },
    { key: 'extracting_audio', label: 'Extracting Audio (16kHz PCM)' },
    { key: 'transcribing', label: 'Whisper Transcription (INT8 CPU)' },
    { key: 'detecting_scenes', label: 'Scene Boundary Detection' },
    { key: 'analyzing_highlights', label: 'AI Highlight Scoring' },
    { key: 'selecting_clips', label: 'Optimal Segment Selection' },
    { key: 'rendering_clips', label: 'Vertical Video Rendering & Subtitle Burn' },
    { key: 'completed', label: 'Clips Ready for Download' },
  ];

  const fetchJobs = async () => {
    try {
      const data = await listJobs();
      setJobs(data);

      // If recentJobId was passed or if nothing selected, select first active or recent
      if (recentJobId) {
        const found = data.find((j) => j.id === recentJobId);
        if (found) {
          const detail = await getJobDetails(found.id);
          setSelectedJob(detail);
        }
      } else if (data.length > 0 && !selectedJob) {
        const detail = await getJobDetails(data[0].id);
        setSelectedJob(detail);
      } else if (selectedJob) {
        const detail = await getJobDetails(selectedJob.id);
        setSelectedJob(detail);
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 2000);
    return () => clearInterval(interval);
  }, [recentJobId, selectedJob?.id]);

  const selectJobItem = async (jId) => {
    try {
      const detail = await getJobDetails(jId);
      setSelectedJob(detail);
    } catch (e) {
      console.error(e);
    }
  };

  const getStepStatus = (currentStep, stepKey, jobStatus) => {
    if (jobStatus === 'FAILED') return 'error';
    if (jobStatus === 'COMPLETED') return 'completed';

    const order = stepsPipeline.map((s) => s.key);
    const currIdx = order.indexOf(currentStep);
    const stepIdx = order.indexOf(stepKey);

    if (stepIdx < currIdx) return 'completed';
    if (stepIdx === currIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Processing Queue</h2>
        <p className="text-sm text-slate-400 mt-1">
          Monitor real-time AI transcription, scene cutting, highlight scoring, and FFmpeg vertical rendering progress.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Job History List */}
        <div className="lg:col-span-1 bg-[#131A2B] border border-slate-800 rounded-2xl p-5 h-fit shadow-md">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <ListOrdered className="w-4 h-4 text-[#747CFF]" />
            <span>Jobs Queue ({jobs.length})</span>
          </h3>

          {loading ? (
            <div className="py-8 flex justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-[#747CFF]" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No jobs in queue. Create one to see live progress.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {jobs.map((job) => {
                const isSelected = selectedJob?.id === job.id;
                const isProcessing = job.status === 'PROCESSING' || job.status === 'QUEUED';
                return (
                  <div
                    key={job.id}
                    onClick={() => selectJobItem(job.id)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'bg-[#747CFF]/15 border-[#747CFF]'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-white truncate max-w-[170px]">
                        {job.project_title || job.id}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          job.status === 'COMPLETED'
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : job.status === 'FAILED'
                            ? 'bg-red-500/15 text-red-400'
                            : 'bg-amber-500/15 text-amber-400'
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(job.created_at).toLocaleTimeString()}
                      </span>
                      <span className="font-medium text-slate-300">
                        {Math.round(job.progress)}%
                      </span>
                    </div>

                    {isProcessing && (
                      <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-[#747CFF] h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Active Job Details & Pipeline Visualizer */}
        <div className="lg:col-span-2 space-y-6">
          {selectedJob ? (
            <div className="bg-[#131A2B] border border-slate-800 rounded-2xl p-6 shadow-md space-y-6">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-[#9B9EFF]">
                      Job ID: {selectedJob.id}
                    </span>
                    <span className="text-xs text-slate-500">•</span>
                    <span className="text-xs text-slate-400">
                      {selectedJob.aspect_ratio} • {selectedJob.clip_duration}s per clip
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white">
                    {selectedJob.project_title}
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  {selectedJob.status === 'COMPLETED' && (
                    <>
                      <a
                        href={getZipDownloadUrl(selectedJob.id)}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl brand-gradient brand-gradient-hover text-white text-xs font-semibold glow-primary shadow transition cursor-pointer"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download All (ZIP)</span>
                      </a>
                      <button
                        onClick={() => {
                          setSelectedProjectId(selectedJob.project_id);
                          setActiveTab('clips');
                        }}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition cursor-pointer"
                      >
                        <span>View Clips</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Progress Summary Bar */}
              <div>
                <div className="flex justify-between items-center text-sm font-semibold mb-2">
                  <span className="text-slate-300">
                    {selectedJob.status === 'COMPLETED'
                      ? 'AI Clipping Pipeline Finished'
                      : selectedJob.status === 'FAILED'
                      ? 'Processing Failed'
                      : 'Processing Pipeline in Progress...'}
                  </span>
                  <span className="text-[#9B9EFF] font-bold">
                    {Math.round(selectedJob.progress)}%
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden p-0.5 border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      selectedJob.status === 'FAILED'
                        ? 'bg-red-500'
                        : selectedJob.status === 'COMPLETED'
                        ? 'bg-emerald-400'
                        : 'brand-gradient'
                    }`}
                    style={{ width: `${selectedJob.progress}%` }}
                  />
                </div>
              </div>

              {/* Error Box if Failed */}
              {selectedJob.error_message && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-start gap-3">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-semibold block mb-0.5">Pipeline Error:</strong>
                    <span>{selectedJob.error_message}</span>
                  </div>
                </div>
              )}

              {/* Step By Step Pipeline Visualizer */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                  Step-by-Step AI Execution
                </h4>
                <div className="space-y-3">
                  {stepsPipeline.map((step, idx) => {
                    const status = getStepStatus(selectedJob.current_step, step.key, selectedJob.status);
                    return (
                      <div
                        key={step.key}
                        className={`flex items-center justify-between p-3.5 rounded-xl border transition ${
                          status === 'active'
                            ? 'bg-[#747CFF]/15 border-[#747CFF]'
                            : status === 'completed'
                            ? 'bg-slate-900/40 border-slate-800/80'
                            : 'bg-slate-900/20 border-slate-800/40 opacity-60'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0">
                            {status === 'completed' ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            ) : status === 'active' ? (
                              <Loader2 className="w-5 h-5 animate-spin text-[#747CFF]" />
                            ) : status === 'error' ? (
                              <AlertCircle className="w-5 h-5 text-red-400" />
                            ) : (
                              <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                            )}
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-white">
                              {step.label}
                            </span>
                          </div>
                        </div>

                        <div>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                              status === 'completed'
                                ? 'text-emerald-400 bg-emerald-500/10'
                                : status === 'active'
                                ? 'text-[#9B9EFF] bg-[#747CFF]/20 animate-pulse'
                                : 'text-slate-500'
                            }`}
                          >
                            {status === 'completed' ? 'Done' : status === 'active' ? 'Running' : 'Waiting'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Completed Clips Quick Thumbnails Preview */}
              {selectedJob.clips?.length > 0 && (
                <div className="pt-4 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Generated Clips ({selectedJob.clips.length})
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                    {selectedJob.clips.map((clip) => (
                      <div
                        key={clip.id}
                        onClick={() => {
                          setSelectedProjectId(selectedJob.project_id);
                          setActiveTab('clips');
                        }}
                        className="group relative rounded-xl bg-black overflow-hidden border border-slate-800 hover:border-[#747CFF] transition cursor-pointer"
                      >
                        <div className="aspect-[9/16] w-full">
                          {clip.thumbnail_url ? (
                            <img
                              src={clip.thumbnail_url}
                              alt={clip.title}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center bg-slate-900">
                              <Film className="w-6 h-6 text-slate-600" />
                            </div>
                          )}
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 p-2 flex flex-col justify-between">
                          <span className="self-end px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#747CFF] text-white">
                            {clip.highlight_score}
                          </span>
                          <div>
                            <p className="text-[11px] font-semibold text-white truncate">
                              Clip #{clip.clip_number}
                            </p>
                            <p className="text-[10px] text-slate-300">
                              {clip.duration}s
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-[#131A2B] border border-slate-800 rounded-2xl p-12 text-center text-slate-400 text-sm">
              Select a job from the queue list to inspect live execution details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
