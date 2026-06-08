# 🌿 CleanTrack AI
> **AI-Powered Sanitation Monitoring & Accountability Platform**
CleanTrack AI uses **YOLOv8** computer vision to verify garbage reports submitted by citizens, enabling authorities to manage complaints and administrators to monitor sanitation performance city-wide.
---
## 📁 Project Structure
```
CleanTrackAI/
│
├── app.py                    ← Flask backend (main application)
├── database.db               ← SQLite database (auto-created on first run)
├── requirements.txt          ← Python dependencies
├── run.bat                   ← Windows one-click setup & run script
│
├── templates/
│   ├── index.html            ← Landing page
│   ├── citizen.html          ← Complaint submission portal
│   ├── track.html            ← Complaint status tracking
│   ├── authority.html        ← Authority management dashboard
│   └── admin.html            ← Admin analytics dashboard
│
├── static/
│   ├── css/
│   │   └── style.css         ← Global design system (dark theme)
│   ├── js/
│   │   └── main.js           ← Geolocation, drag-drop, modals, charts
│   └── uploads/              ← Uploaded complaint images (auto-created)
│
└── ai/
    ├── __init__.py
    └── garbage_detection.py  ← YOLOv8 + OpenCV detection module
```
---
## 🚀 Quick Start
### Option 1: Double-click `run.bat` (Windows)
Just double-click `run.bat` — it will:
1. Create a Python virtual environment
2. Install all dependencies
3. Start the Flask server
Then open: **http://127.0.0.1:5000**
---
### Option 2: Manual Setup
```bash
# 1. Create a virtual environment
python -m venv venv
# 2. Activate it (Windows)
venv\Scripts\activate
# 3. Install dependencies
pip install -r requirements.txt
# 4. Run the app
python app.py
```
Open **http://127.0.0.1:5000** in your browser.
---
## 🌐 Pages & Routes
|
 URL 
|
 Description 
|
|
-----
|
-------------
|
|
`/`
|
 Home / Landing page 
|
|
`/citizen`
|
 Citizen complaint submission 
|
|
`/track/<id>`
|
 Track specific complaint 
|
|
`/authority`
|
 Authority management dashboard 
|
|
`/admin`
|
 Admin analytics dashboard 
|
|
`/api/stats`
|
 JSON stats API (for charts) 
|
|
`/api/complaints/search?id=N`
|
 Search complaint by ID 
|
---
## ✨ Features
### 👤 Citizen Portal
- Upload garbage image (drag & drop supported)
- Auto-capture GPS location via browser geolocation
- Enter location name and description
- Submit complaint → get a complaint ID
- Track complaint status by ID
### 🤖 AI Verification
- YOLOv8 analyzes uploaded image
- Returns: **Garbage Detected** / **No Garbage Detected**
- Falls back to OpenCV heuristics if ultralytics unavailable
### 🏛️ Authority Dashboard
- View all complaints with filters (All / Pending / In Progress / Resolved / Escalated)
- View image, GPS, description, AI result
- Update complaint status
- Upload resolution proof image
- Clickable image lightbox
### ⚙️ Admin Dashboard
- Stat cards: Total / Pending / In Progress / Resolved / Escalated / Last 7 Days
- Resolution rate progress bar
- Chart.js donut chart (status breakdown)
- 14-day submission trend line chart
- Full complaints table with delete action
### 🚨 Escalation Logic
- Complaints in **Pending** or **In Progress** status for **10+ days** are automatically marked **Escalated**
- Runs automatically on every page load
---
## 🗄️ Database Schema
```sql
CREATE TABLE complaints (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    image            TEXT NOT NULL,           -- uploaded filename
    latitude         REAL,                    -- GPS latitude
    longitude        REAL,                    -- GPS longitude
    description      TEXT,                    -- citizen description
    status           TEXT DEFAULT 'Pending',  -- Pending/In Progress/Resolved/Escalated
    date             TEXT NOT NULL,           -- submission timestamp
    ai_result        TEXT DEFAULT 'Pending',  -- AI detection label
    ai_confidence    REAL DEFAULT 0.0,        -- AI confidence score
    resolution_image TEXT,                    -- authority proof image filename
    location_name    TEXT                     -- optional human-readable location
);
```
---
## 🤖 AI Detection Module
The `ai/garbage_detection.py` module:
1. Loads **YOLOv8 nano** model (`yolov8n.pt`) via `ultralytics`
2. Runs inference on the uploaded image
3. Checks detected objects against garbage-related COCO classes
4. Returns confidence score and detection label
5. **Fallback**: Uses OpenCV color/texture heuristics if YOLOv8 is unavailable
---
## 📦 Dependencies
|
 Package 
|
 Purpose 
|
|
---------
|
---------
|
|
 Flask 2.3 
|
 Web framework 
|
|
 Werkzeug 
|
 File upload security 
|
|
 ultralytics 
|
 YOLOv8 model 
|
|
 opencv-python 
|
 Image processing 
|
|
 Pillow 
|
 Image handling 
|
|
 numpy 
|
 Array operations 
|
|
 Chart.js (CDN) 
|
 Dashboard charts 
|
---
## 🎨 Design
- **Dark glassmorphism** theme with green accent (`#22c55e`)
- **Space Grotesk + Inter** typography (Google Fonts)
- Smooth hover animations and micro-interactions
- Fully responsive (mobile-friendly)
- Counter animations on admin stats
---
## 📝 Notes
- First run auto-downloads `yolov8n.pt` (~6MB) from Ultralytics
- Uploaded images stored in `static/uploads/`
- Database is auto-initialized on first `python app.py`
- No authentication — add Flask-Login for production use