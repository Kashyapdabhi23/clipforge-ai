import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Link as LinkIcon, 
  Sparkles, 
  Clock, 
  Film, 
  Globe2, 
  Type, 
  Layers, 
  AlertCircle,
  CheckCircle2,
  FileVideo,
  Loader2
} from 'lucide-react';
import { uploadVideoFile, uploadVideoUrl, createClippingJob } from '../services/api';

export default function CreateClips({ setActiveTab, setRecentJobId }) {
  // Input method: 'upload' | 'url'
  const [inputMethod, setInputMethod] = useState('upload');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedProject, setUploadedProject] = useState(null);

  // URL State
  const [videoUrl, setVideoUrl] = useState('');
  const [rapidApiKey, setRapidApiKey] = useState(() => localStorage.getItem('clipforge_rapidapi_key') || '87b03191b7msh0cb73dee47495ccp186ff6jsn2c0a2eed2f31');
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [isUrlIngesting, setIsUrlIngesting] = useState(false);

  // Processing Settings
  const [clipDuration, setClipDuration] = useState(30);
  const [clipCount, setClipCount] = useState(5);
  const [customClipCount, setCustomClipCount] = useState('');
  const [isCustomCount, setIsCustomCount] = useState(false);
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [language, setLanguage] = useState('auto');
  const [captionStyle, setCaptionStyle] = useState('Modern');

  // Submit / Error states
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    setErrorMsg('');
    const validExtensions = ['.mp4', '.mov', '.mkv', '.webm'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Unsupported file type. Please upload MP4, MOV, MKV, or WEBM.`);
      return;
    }
    // Limit to 10GB
    if (file.size > 10 * 1024 * 1024 * 1024) {
      setErrorMsg('File size exceeds 10 GB limit.');
      return;
    }
    setSelectedFile(file);
    setUploadedProject(null);
  };

  // Perform upload
  const handleUploadFile = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMsg('');
    try {
      const res = await uploadVideoFile(selectedFile, (progress) => {
        setUploadProgress(progress);
      });
      setUploadedProject(res);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to upload video file.');
    } finally {
      setIsUploading(false);
    }
  };

  // Ingest URL
  const handleIngestUrl = async () => {
    let raw = videoUrl.trim();
    if (!raw) {
      setErrorMsg('Please enter a valid video URL.');
      return;
    }

    // Auto-clean if URL was duplicated on paste
    const httpMatches = raw.match(/https?:\/\/[^\s]+/g);
    if (httpMatches && httpMatches.length > 0) {
      let first = httpMatches[0];
      const secondHttp = first.indexOf('http', 4);
      if (secondHttp !== -1) {
        first = first.substring(0, secondHttp);
      }
      raw = first.trim();
      setVideoUrl(raw);
    }

    setIsUrlIngesting(true);
    setErrorMsg('');
    try {
      if (rapidApiKey) {
        localStorage.setItem('clipforge_rapidapi_key', rapidApiKey.trim());
      }
      const res = await uploadVideoUrl(raw, rapidApiKey.trim() || null);
      setUploadedProject(res);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to ingest video from URL.');
    } finally {
      setIsUrlIngesting(false);
    }
  };

  // Generate AI Clips
  const handleGenerateClips = async () => {
    if (!uploadedProject?.project_id) {
      setErrorMsg('Please upload or ingest a video before generating clips.');
      return;
    }

    const finalClipCount = isCustomCount ? parseInt(customClipCount, 10) || 5 : clipCount;

    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const res = await createClippingJob({
        project_id: uploadedProject.project_id,
        clip_duration: clipDuration,
        requested_clips: finalClipCount,
        aspect_ratio: aspectRatio,
        language: language,
        caption_style: captionStyle,
      });

      if (res.job_id) {
        setRecentJobId(res.job_id);
        setActiveTab('queue');
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to start AI clipping job.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Create AI Clips</h2>
        <p className="text-sm text-slate-400 mt-1">
          Upload video footage or paste a public link, configure clipping preferences, and let AI generate multiple vertical highlights.
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Input Method Selector */}
      <div className="p-1.5 rounded-xl bg-[#131A2B] border border-slate-800 inline-flex gap-1">
        <button
          onClick={() => { setInputMethod('upload'); setErrorMsg(''); }}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition cursor-pointer ${
            inputMethod === 'upload' ? 'bg-[#747CFF] text-white shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Upload Video File</span>
        </button>
        <button
          onClick={() => { setInputMethod('url'); setErrorMsg(''); }}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition cursor-pointer ${
            inputMethod === 'url' ? 'bg-[#747CFF] text-white shadow-md' : 'text-slate-400 hover:text-white'
          }`}
        >
          <LinkIcon className="w-4 h-4" />
          <span>Authorized Video URL</span>
        </button>
      </div>

      {/* Video Source Card */}
      <div className="p-6 rounded-2xl bg-[#131A2B] border border-slate-800 shadow-md">
        {uploadedProject ? (
          /* Ready Video Preview Card */
          <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30">
            <div className="w-28 h-32 rounded-lg bg-black shrink-0 overflow-hidden relative border border-slate-700">
              {uploadedProject.thumbnail_url ? (
                <img
                  src={uploadedProject.thumbnail_url}
                  alt="Thumbnail"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <FileVideo className="w-8 h-8 text-slate-500" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0 text-center sm:text-left">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold mb-2">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Video Ready for AI Processing</span>
              </div>
              <h3 className="text-base font-bold text-white truncate">
                {uploadedProject.title || uploadedProject.filename}
              </h3>
              <div className="mt-2 flex flex-wrap items-center justify-center sm:justify-start gap-4 text-xs text-slate-400">
                <span>Duration: <strong className="text-slate-200">{Math.round(uploadedProject.duration)}s</strong></span>
                <span>•</span>
                <span>Size: <strong className="text-slate-200">{uploadedProject.file_size_mb} MB</strong></span>
                <span>•</span>
                <span>Resolution: <strong className="text-slate-200">{uploadedProject.width}x{uploadedProject.height}</strong></span>
              </div>
            </div>
            <button
              onClick={() => { setUploadedProject(null); setSelectedFile(null); }}
              className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
            >
              Change Video
            </button>
          </div>
        ) : inputMethod === 'upload' ? (
          /* Drag and Drop Upload Zone */
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-[#747CFF] rounded-xl p-10 text-center transition cursor-pointer bg-slate-900/40 hover:bg-slate-900/70"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.mov,.mkv,.webm"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="w-14 h-14 rounded-2xl bg-[#747CFF]/10 text-[#747CFF] flex items-center justify-center mx-auto mb-4">
              <Upload className="w-7 h-7" />
            </div>
            <p className="text-sm font-semibold text-white">
              {selectedFile ? selectedFile.name : 'Click or Drag & Drop Video File Here'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports MP4, MOV, MKV, and WEBM (Up to 10 GB)
            </p>

            {selectedFile && !isUploading && (
              <div className="mt-4">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleUploadFile();
                  }}
                  className="px-6 py-2.5 rounded-xl brand-gradient brand-gradient-hover text-white text-xs font-semibold glow-primary shadow-md cursor-pointer"
                >
                  Upload & Analyze File ({Math.round(selectedFile.size / (1024 * 1024))} MB)
                </button>
              </div>
            )}

            {isUploading && (
              <div className="mt-4 max-w-xs mx-auto">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Uploading video...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-[#747CFF] h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          /* URL Ingestion Field */
          <div className="space-y-4">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              Authorized Video URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="https://example.com/video.mp4 or terms-compliant public link"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-[#747CFF]"
              />
              <button
                type="button"
                onClick={handleIngestUrl}
                disabled={isUrlIngesting}
                className="px-6 py-3 rounded-xl brand-gradient brand-gradient-hover text-white text-sm font-semibold glow-primary disabled:opacity-50 transition cursor-pointer flex items-center gap-2"
              >
                {isUrlIngesting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Fetching...</span>
                  </>
                ) : (
                  <span>Fetch Video</span>
                )}
              </button>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowApiKeyInput(!showApiKeyInput)}
                className="text-xs text-[#9B9EFF] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>{showApiKeyInput ? 'Hide YouTube API Settings' : '+ Configure RapidAPI Key for YouTube links'}</span>
              </button>

              {showApiKeyInput && (
                <div className="mt-3 p-3.5 rounded-xl bg-slate-900/90 border border-slate-700/80 space-y-2">
                  <label className="text-[11px] font-semibold text-slate-300 block">
                    RapidAPI YouTube Downloader Key
                  </label>
                  <input
                    type="password"
                    placeholder="Enter RapidAPI Key (e.g. 748afc8...)"
                    value={rapidApiKey}
                    onChange={(e) => {
                      setRapidApiKey(e.target.value);
                      localStorage.setItem('clipforge_rapidapi_key', e.target.value);
                    }}
                    className="w-full px-3 py-2 rounded-lg bg-black/50 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#747CFF]"
                  />
                  <p className="text-[10px] text-slate-400 leading-relaxed">
                    Uses RapidAPI ("YouTube Media Downloader") proxy to bypass ISP/YouTube connection drops. Free tiers are available on rapidapi.com.
                  </p>
                </div>
              )}
            </div>

            <p className="text-xs text-slate-500">
              Only terms-compliant, DRM-free, or authorized direct public video links are supported.
            </p>
          </div>
        )}
      </div>

      {/* AI Settings Section */}
      <div className="p-6 rounded-2xl bg-[#131A2B] border border-slate-800 space-y-6 shadow-md">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#747CFF]" />
          <span>Clip Generation Settings</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Clip Duration */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#747CFF]" />
              Clip Duration
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[15, 30, 45, 60].map((dur) => (
                <button
                  key={dur}
                  type="button"
                  onClick={() => setClipDuration(dur)}
                  className={`py-2.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
                    clipDuration === dur
                      ? 'bg-[#747CFF] border-[#747CFF] text-white shadow-md'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  {dur}s {dur === 30 && <span className="text-[10px] block opacity-80">(Default)</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Number of Clips */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#747CFF]" />
              Number of Clips
            </label>
            <div className="grid grid-cols-6 gap-1.5">
              {[3, 5, 10, 15, 20].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => { setClipCount(count); setIsCustomCount(false); }}
                  className={`py-2 rounded-lg text-xs font-semibold border transition cursor-pointer ${
                    !isCustomCount && clipCount === count
                      ? 'bg-[#747CFF] border-[#747CFF] text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  {count}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setIsCustomCount(true)}
                className={`py-2 rounded-lg text-xs font-semibold border transition cursor-pointer ${
                  isCustomCount
                    ? 'bg-[#747CFF] border-[#747CFF] text-white'
                    : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                Custom
              </button>
            </div>
            {isCustomCount && (
              <input
                type="number"
                min="1"
                max="30"
                placeholder="Enter custom count (e.g. 7)"
                value={customClipCount}
                onChange={(e) => setCustomClipCount(e.target.value)}
                className="mt-2 w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-[#747CFF]"
              />
            )}
          </div>

          {/* Aspect Ratio */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5 flex items-center gap-1.5">
              <Film className="w-3.5 h-3.5 text-[#747CFF]" />
              Aspect Ratio
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: '9:16', label: '9:16 Vertical', desc: 'Shorts, Reels, TikTok' },
                { id: '1:1', label: '1:1 Square', desc: 'Instagram Feed' },
                { id: '16:9', label: '16:9 Landscape', desc: 'YouTube Standard' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setAspectRatio(item.id)}
                  className={`p-3 rounded-xl text-left border transition cursor-pointer ${
                    aspectRatio === item.id
                      ? 'bg-[#747CFF]/20 border-[#747CFF] text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-xs">{item.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{item.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Language & Captions */}
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                <Globe2 className="w-3.5 h-3.5 text-[#747CFF]" />
                Audio Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-[#747CFF] cursor-pointer"
              >
                <option value="auto">Auto Detect Language</option>
                <option value="en">English</option>
                <option value="hi">Hindi (हिंदी)</option>
                <option value="gu">Gujarati (ગુજરાતી)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                <Type className="w-3.5 h-3.5 text-[#747CFF]" />
                Caption Style
              </label>
              <div className="grid grid-cols-5 gap-1.5">
                {['Modern', 'Bold', 'Minimal', 'Gaming', 'Podcast'].map((style) => (
                  <button
                    key={style}
                    type="button"
                    onClick={() => setCaptionStyle(style)}
                    className={`py-2 rounded-lg text-xs font-semibold border transition cursor-pointer ${
                      captionStyle === style
                        ? 'bg-[#747CFF] border-[#747CFF] text-white'
                        : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={handleGenerateClips}
            disabled={!uploadedProject || isSubmitting}
            className={`w-full py-4 rounded-xl font-bold text-sm tracking-wide transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer shadow-xl ${
              uploadedProject && !isSubmitting
                ? 'brand-gradient brand-gradient-hover text-white glow-primary'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Launching AI Engine Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Generate AI Clips</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
