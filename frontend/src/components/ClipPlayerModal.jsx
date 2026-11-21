import React, { useState } from 'react';
import { 
  X, 
  Download, 
  FileText, 
  Sparkles, 
  Clock, 
  Film, 
  Trash2,
  CheckCircle2
} from 'lucide-react';
import { getClipDownloadUrl, getSubtitleDownloadUrl, resolveMediaUrl } from '../services/api';

export default function ClipPlayerModal({ clip, onClose, onDelete }) {
  const [downloadFormat, setDownloadFormat] = useState('srt');
  const [copied, setCopied] = useState(false);

  if (!clip) return null;

  const handleCopyTranscript = () => {
    if (clip.transcript) {
      navigator.clipboard.writeText(clip.transcript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 60) return 'text-[#9B9EFF] bg-[#747CFF]/10 border-[#747CFF]/30';
    return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#131A2B] border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col md:flex-row shadow-2xl glow-card">
        
        {/* Left Side: Video Preview (9:16 Vertical responsive player) */}
        <div className="md:w-1/2 bg-black flex items-center justify-center relative min-h-[380px] p-2">
          <video
            src={resolveMediaUrl(clip.video_url)}
            controls
            autoPlay
            loop
            className="max-h-[75vh] w-auto max-w-full rounded-xl object-contain shadow-lg"
          />
        </div>

        {/* Right Side: Clip Metadata, AI Scoring, Subtitles & Actions */}
        <div className="md:w-1/2 p-6 flex flex-col justify-between overflow-y-auto">
          <div>
            {/* Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-[#747CFF]/20 text-[#9B9EFF]">
                    Clip #{clip.clip_number}
                  </span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {clip.duration}s
                  </span>
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Film className="w-3 h-3" />
                    {clip.aspect_ratio || '9:16'}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white leading-tight">
                  {clip.title}
                </h3>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* AI Highlight Scoring Card */}
            <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#747CFF]" />
                  AI Highlight Score
                </span>
                <span className={`text-sm font-bold px-2.5 py-0.5 rounded-full border ${getScoreColor(clip.highlight_score)}`}>
                  {clip.highlight_score} / 100
                </span>
              </div>
              {clip.reasoning && (
                <p className="text-xs text-slate-300 leading-relaxed font-medium">
                  {clip.reasoning}
                </p>
              )}
            </div>

            {/* Transcript Preview */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Transcript
                </label>
                <button
                  onClick={handleCopyTranscript}
                  className="text-xs text-[#9B9EFF] hover:text-white flex items-center gap-1 transition cursor-pointer"
                >
                  {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <FileText className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-300 leading-relaxed max-h-36 overflow-y-auto">
                {clip.transcript || 'No transcript generated for this clip segment.'}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-6 pt-4 border-t border-slate-800 space-y-3">
            <div className="flex items-center gap-2">
              {/* Download Video Button */}
              <a
                href={getClipDownloadUrl(clip.id)}
                download
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl brand-gradient brand-gradient-hover text-white text-xs font-semibold glow-primary transition cursor-pointer shadow-md"
              >
                <Download className="w-4 h-4" />
                <span>Download MP4</span>
              </a>

              {/* Subtitles Download */}
              <a
                href={getSubtitleDownloadUrl(clip.id, 'srt')}
                download
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition cursor-pointer"
                title="Download SRT Subtitle"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>SRT</span>
              </a>

              <a
                href={getSubtitleDownloadUrl(clip.id, 'vtt')}
                download
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition cursor-pointer"
                title="Download VTT Subtitle"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>VTT</span>
              </a>

              {/* Delete Clip */}
              {onDelete && (
                <button
                  onClick={() => onDelete(clip.id)}
                  className="p-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition cursor-pointer"
                  title="Delete Clip"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
