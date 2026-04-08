Below is a **Codex-ready implementation spec** with explicit structure, contracts, and acceptance criteria.

---

# Implementation Spec: Personal Capture & Insight System

## 1. System Overview

A real-time personal knowledge system that:

* Captures **speech**, **screenshots**, and **manual inputs**
* Enriches data using **LLM + web context**
* Performs **continuous analysis** for insights
* Displays everything in a **live timeline (rolling canvas)**
* Provides an **end-of-day voice review workflow**

---

## 2. Tech Stack

### Backend

* Python (FastAPI)
* PostgreSQL (primary DB)
* Redis (queues / real-time events)
* Celery or RQ (background jobs)

### Frontend

* Next.js (App Router)
* TypeScript
* WebSockets (live updates)

### AI / External APIs

* OpenAI API:

  * Speech-to-text
  * Summarization
  * Reasoning / insights
  * Voice chat
* Gemini API:

  * Screenshot / multimodal analysis
* Optional:

  * Nano Banana (graph/visual generation)

---

## 3. High-Level Architecture

```
[Client]
  ├── Audio Stream
  ├── Screenshot Hook
  ├── UI Actions
        ↓
[API Gateway - FastAPI]
        ↓
[Ingestion Layer]
  ├── Audio სამსახ → Transcription სამსახ
  ├── Screenshot → Vision Analysis
        ↓
[Enrichment Layer]
        ↓
[Analysis Layer]
        ↓
[Storage Layer - PostgreSQL]
        ↓
[Realtime Layer - Redis/WebSocket]
        ↓
[Next.js Frontend Timeline]
```

---

## 4. Core Services

### 4.1 Ingestion Service

**Responsibilities:**

* Accept raw inputs
* Normalize into internal format

#### Endpoints

```http
POST /ingest/audio
POST /ingest/screenshot
POST /ingest/text
```

#### Audio Flow

1. Receive audio chunk
2. Send to OpenAI transcription
3. Store raw transcript
4. Emit event → enrichment queue

#### Screenshot Flow

1. Receive image + metadata
2. Store image
3. Send to Gemini for:

   * OCR
   * UI understanding
   * Context inference
4. Emit event → enrichment queue

---

### 4.2 Enrichment Service

**Responsibilities:**

* Add context to entries

#### Tasks

* Keyword extraction
* Entity detection
* Optional web search
* Context linking

#### Output

```json
{
  "summary": "...",
  "tags": ["ai", "project-x"],
  "related_entries": ["uuid1", "uuid2"],
  "external_context": "...",
  "confidence": 0.82
}
```

---

### 4.3 Analysis Service

Runs periodically + on new data.

**Detect:**

* Trends
* Repeated topics
* Open loops
* Task clusters
* Missed opportunities

#### Insight Object

```json
{
  "type": "trend | reminder | contradiction | opportunity",
  "title": "...",
  "description": "...",
  "related_entries": [],
  "priority": 1-5,
  "confidence": 0.0-1.0
}
```

---

### 4.4 Visualization Service

Trigger condition:

* High relationship density between entries

**Output:**

* Graph JSON or image

```json
{
  "nodes": [],
  "edges": []
}
```

Optional:

* Call Nano Banana API for rendering

---

### 4.5 End-of-Day Review Service

Trigger:

```http
POST /review/start
```

**Flow:**

1. Aggregate day’s entries
2. Generate:

   * Summary
   * Key insights
   * Unresolved items
3. Start voice session
4. Accept user corrections

---

## 5. Data Model

### Entry

```sql
entries (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMP,
  type TEXT, -- audio | screenshot | text | analysis
  raw_content TEXT,
  enriched_content JSONB,
  tags TEXT[],
  project TEXT,
  relationships UUID[],
  confidence FLOAT,
  metadata JSONB,
  created_at TIMESTAMP
)
```

### Insights

```sql
insights (
  id UUID PRIMARY KEY,
  type TEXT,
  title TEXT,
  description TEXT,
  related_entries UUID[],
  priority INT,
  confidence FLOAT,
  created_at TIMESTAMP
)
```

### Screenshots

```sql
screenshots (
  id UUID PRIMARY KEY,
  entry_id UUID,
  file_path TEXT,
  ocr_text TEXT,
  analysis JSONB
)
```

---

## 6. Realtime Layer

* WebSocket endpoint:

```http
/ws/timeline
```

**Events:**

* `entry_created`
* `entry_updated`
* `insight_created`

---

## 7. Frontend (Next.js)

### Pages

```
/app
  /timeline
  /review
  /insights
  /settings
```

### Core Components

* TimelineCanvas
* EntryCard
* InsightPanel
* VoiceReviewPanel
* ScreenshotViewer

### Timeline Behavior

* Infinite vertical scroll
* Live updates via WebSocket
* Filter by:

  * type
  * tags
  * project

---

## 8. Pipelines

### 8.1 Audio Pipeline

```
Audio → Transcription → Entry → Enrichment → Analysis → Timeline
```

### 8.2 Screenshot Pipeline

```
Screenshot → Gemini Analysis → Entry → Enrichment → Analysis → Timeline
```

---

## 9. Security & Privacy

* Explicit user consent before:

  * audio recording
  * screenshot capture
* Local encryption for sensitive data
* Token-based authentication (JWT)
* Audit log of:

  * edits
  * deletions
  * AI modifications

---

## 10. Folder Structure

### Backend

```
backend/
  app/
    main.py
    api/
      routes_ingest.py
      routes_review.py
    services/
      transcription.py
      enrichment.py
      analysis.py
      vision.py
      insights.py
    models/
    db/
    workers/
  requirements.txt
```

### Frontend

```
frontend/
  app/
    timeline/
    review/
    insights/
  components/
  lib/
  hooks/
```

---

## 11. Acceptance Criteria

### Core Functionality

* [ ] Audio is transcribed in near real-time (<2s delay)
* [ ] Screenshots are stored and analyzed automatically
* [ ] Entries appear in timeline within 1–3 seconds
* [ ] Enrichment adds tags + summaries
* [ ] Insights are generated automatically

### UX

* [ ] Timeline updates live without refresh
* [ ] User can edit/delete entries
* [ ] End-of-day review produces usable summary

### Intelligence

* [ ] System detects at least:

  * repeated topics
  * unfinished tasks
  * cross-entry relationships

### Reliability

* [ ] System handles background job failures gracefully
* [ ] No data loss on restart

---

## 12. Stretch Goals

* Local-first mode (offline capture)
* Mobile companion app
* Plugin system for new data sources
* Calendar + email integration
* Semantic search (vector DB)

---

If needed, this can be expanded into:

* **Step-by-step Codex task breakdown**
* **Initial code scaffolding (FastAPI + Next.js)**
* **Database migrations + schemas**
* **Docker setup**
