# ClipForge AI – Automated AI Video Clipper Website

**ClipForge AI** is a production-grade, full-stack automated AI video highlight generator and short video repurposing platform. It automatically processes long-form videos, identifies the most engaging viral moments using speech recognition, scene cut analysis, and NLP highlight heuristics, and renders multiple vertical (9:16) 1080x1920 MP4 video clips with synchronized subtitle burns.

---

## ⚡ Key Highlights & Capabilities

- **Automated AI Highlight Detection**: Multi-factor scoring engine analyzing transcript sentiment, questions & answers, excitement spikes, speech density, and scene boundaries.
- **Multiple High-Quality Clips**: Generates multiple independent clips (3, 5, 10, 15, 20, or custom count) with intelligent non-overlapping time boundaries.
- **9:16 Vertical Video Reframing**: Converts landscape/wide video into vertical 1080x1920 shorts using intelligent center cropping. Also supports 1:1 square and 16:9 landscape.
- **Automated Subtitles & Captions**: Synchronized caption generation with customizable typography styles:
  - *Modern*
  - *Bold*
  - *Minimal*
  - *Gaming*
  - *Podcast*
  - Multi-language support (English, Hindi, Gujarati, and Auto-Detect).
  - Standalone `.srt` and `.vtt` downloads.
- **Targeted Hardware Optimization (8 GB RAM / Intel Core i5)**:
  - **faster-whisper** with `tiny` INT8 CPU quantization (~75 MB RAM footprint).
  - **FFmpeg** `ultrafast` preset with strict thread limits (2 threads) to prevent CPU starvation.
  - **Single-Job Worker Semaphore**: Enforces 1 heavy processing job at a time, protecting system responsiveness.
  - **Chunked File Streaming**: Direct streaming to disk without buffering full videos in RAM.
  - Automatic intermediate file cleanup.
- **Modern Dark UI/UX Dashboard**:
  - Palette: `#090D18` background, `#131A2B` card, `#747CFF` primary, `#9B9EFF` accent, `#F4F6FF` text.
  - Real-time processing queue with step-by-step progress tracking.
  - Video preview modal, batch ZIP downloads, project history management.

---

## 🏗️ Architecture & Project Structure

```
D:/clipforge-ai/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API endpoints (upload, jobs, projects, clips, health)
│   │   ├── core/                # Configuration, hardware settings, logging
│   │   ├── database/            # SQLAlchemy database engine & session
│   │   ├── models/              # SQLite / Postgres models (User, Project, Video, Job, Clip, Subtitle)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Background job queue, disk storage management
│   │   ├── ai/                  # faster-whisper INT8 service, PySceneDetect highlight engine
│   │   ├── video/               # FFmpeg cropping, subtitle styling, metadata probing
│   │   └── main.py              # FastAPI application entrypoint & static mounting
│   ├── storage/                 # Uploads, rendered clips, thumbnails, temp audio
│   └── venv/                    # Python virtual environment
├── frontend/
│   ├── src/
│   │   ├── components/          # Sidebar, Navbar, VideoPlayerModal
│   │   ├── pages/               # Dashboard, CreateClips, MyProjects, AllClips, Queue, Settings
│   │   ├── services/            # Axios API client
│   │   ├── App.jsx              # Main React application
│   │   └── index.css            # Tailwind CSS styling & brand themes
│   ├── package.json
│   └── vite.config.js           # Vite dev server with proxy to backend
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
├── run_backend.bat              # Windows batch file to start FastAPI backend
├── run_frontend.bat             # Windows batch file to start React Vite frontend
├── start_clipforge.bat          # Single-click launcher for both backend & frontend
└── README.md
```

---

## 🚀 Quick Start Guide (Windows)

### Prerequisites

1. **Python 3.10+** (Python 3.12, 3.13, or 3.14 recommended)
2. **Node.js 18+** & npm

---

### Step 1: Backend Setup

Open PowerShell or Command Prompt:

```cmd
cd /d D:\clipforge-ai\backend

:: If venv is not yet created:
python -m venv venv

:: Activate environment
call venv\Scripts\activate

:: Install required packages
pip install -r ..\requirements.txt
```

Start the Backend server:

```cmd
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The API will be live at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Frontend Setup

Open a second terminal window:

```cmd
cd /d D:\clipforge-ai\frontend

:: Install Node packages (already completed)
npm install

:: Start the Vite development server
npm run dev
```

*The web dashboard will be available at `http://localhost:5173`.*

---

### Step 3: Single-Click Launch (All-In-One)

Double click:
```
D:\clipforge-ai\start_clipforge.bat
```
This automatically launches both the backend API server and frontend server and opens the dashboard in your browser.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Multipart file upload (MP4, MOV, MKV, WEBM) |
| `POST` | `/api/upload/url` | Authorized public video URL ingestion |
| `POST` | `/api/jobs` | Submit AI clipping job with preferences |
| `GET` | `/api/jobs` | List all processing jobs |
| `GET` | `/api/jobs/{job_id}` | Real-time step progress and results |
| `GET` | `/api/jobs/{job_id}/download` | Download all clips of a job as a single ZIP |
| `GET` | `/api/projects` | List all projects with clip counts |
| `GET` | `/api/projects/{project_id}` | Get project details and clips |
| `DELETE` | `/api/projects/{project_id}` | Delete project and remove media files |
| `GET` | `/api/clips` | List all generated clips across all projects |
| `GET` | `/api/clips/{clip_id}/download` | Download single clip MP4 |
| `GET` | `/api/clips/{clip_id}/subtitles` | Download standalone SRT/VTT subtitle |
| `DELETE` | `/api/clips/{clip_id}` | Delete individual clip |
| `GET` | `/api/health` | Backend subsystems and FFmpeg readiness |
| `GET` | `/api/stats` | Aggregated dashboard analytics |

---

## ⚙️ AI Video Processing Pipeline Details

1. **Audio Extraction**: FFmpeg extracts 16kHz 16-bit mono PCM audio from the source video.
2. **Speech Recognition**: `faster-whisper` (tiny model, CPU INT8) generates word-level and segment-level timestamps with language detection.
3. **Scene Cut Detection**: `PySceneDetect` detects visual scene transitions so clip boundaries don't break abruptly.
4. **Heuristic Highlight Scoring**:
   - Question and Answer pairs (`?`, "why", "how", "kya", "kem").
   - Emotional punchlines, strong reactions, and exclamations (`!`, "unbelievable", "secret", "zabardast").
   - High-energy gaming and storytelling moments.
   - Speech rate calculation (~2.2 to 3.8 words/second optimal pacing).
5. **Non-Overlapping Segment Selection**: Greedily isolates the highest-scoring candidate windows (default 30s) snapped to sentence start/end boundaries.
6. **Smart Cropping & Subtitle Burning**: FFmpeg reframes content into vertical 9:16 (1080x1920) with synchronized burned styled subtitles and exports standard MP4 + standalone SRT/VTT.

---

## 🔒 License & Ethics
- Designed for authorized content repurposing.
- Adheres to terms-of-service compliance for online URLs.
