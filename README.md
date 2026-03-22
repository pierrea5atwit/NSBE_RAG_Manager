# 🧠 Local RAG Backend for Meeting Intelligence

*A fully local, privacy‑preserving Retrieval‑Augmented Generation (RAG) backend designed to ingest meeting notes, generate structured reports, and maintain long‑term organizational memory.*
Built with Python + Flask, Postgres, ChromaDB, and Ollama

Andrew P.

## Features:
- Local LLM + Embeddings via Ollama (Llama 3, Mistral, etc.)
- Vector Search using ChromaDB
- Metadata Storage in Postgres
- Threaded Conversations with persistent memory
- Automatic Task + Event Extraction
- Structured Reports / Outlines / To‑Dos
- Zero external APIs — fully offline, fully free

🏗️ Architecture Overview
## 1. Ingestion
POST /ingest/meeting
- Store meeting metadata
- Store raw document
- Chunk text (500–1000 tokens)
- Embed chunks
- Store embeddings in Chroma
- Store chunk metadata in Postgres

## 2. Query / Chat
POST /query
- Creates a new thread if none provided
- Stores user message
- Runs an intent layer:
- If structured (“October events”, “tasks due this week”) → SQL
- If semantic (“What did we decide about onboarding?”) → RAG
- Retrieves top‑k chunks
- Builds LLM prompt with system instructions + context
- LLM returns structured JSON:
- outline
- report
- todos
- New tasks/events inserted into DB
- Assistant message stored in thread

## 3. Confidence Layer
- If similarity scores < threshold →
“I’m not confident; missing data about X/Y.”

### 🗄️ Database Schema (Postgres)
meetings
- id, title, purpose, participants, platform, category, meeting_time
documents
- id, meeting_id, title, content, purpose
chunks
- id, document_id, chunk_text, position, metadata
(embeddings stored in Chroma)
tasks
- id, meeting_id, description, owners, due_date, status, cmr
events
- id, related_task_ids, event_date, deadline, status, metadata
threads
- id, title, is_open, created_at
messages
- id, thread_id, role, content, created_at

### 🔌 API Endpoints
Ingestion
- POST /ingest/meeting
- POST /ingest/document
Query / Chat
- POST /query
- GET /threads
- GET /threads/<id>
- POST /threads/<id>/message
Tasks / Events
- GET /tasks
- GET /events
- POST /tasks
- PATCH /tasks/<id>
Admin
- GET /health

### 🧰 Tech Stack
- Flask — API layer
- Postgres — metadata + tasks + threads
- ChromaDB — vector storage
- Ollama — local LLM + embeddings
- Docker Compose — orchestration
Everything is free, open‑source, and local‑only.



### Future Notes
If you later move to pgvector, you’d add:

"ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);" to your SQL and skip Chroma.


Here’s a clean, high‑signal snapshot of where your project stands — the **TODOs**, the **completed work**, and the **overall project state**. Think of this as your engineering dashboard.

---

# ✅ **Completed Tasks**

### **Architecture & Design**
- Defined full system architecture (Flask API + Postgres + Chroma + Ollama).
- Designed ingestion → chunking → embedding → vector storage pipeline.
- Designed retrieval → prompt building → LLM JSON output pipeline.
- Defined API endpoint structure (ingestion, query, tasks/events, threads).
- Selected stack components (all free, local, privacy‑preserving).

### **LLM Layer**
- Built strict system prompt aligned with your JSON schema.
- Built user prompt template with context injection.
- Built prompt builder function.
- Built Ollama client (JSON‑safe, system prompt injection, error handling).

### **Vector Store Layer**
- Built embedding module (`SentenceTransformer`).
- Built Chroma client (add_chunk, query).
- Built ingestion pipeline for embeddings → Chroma.

### **JSON Schema**
- Completed v1 schema for:
  - outline  
  - report  
  - todos  
  - events  
  - metadata  
- Schema is deterministic and LLM‑friendly.

### **Project Structure**
- Established clean module layout:
  - `llm/`  
  - `vectorstore/`  
  - `api/`  
- Ensured separation of concerns.

---

# 🟡 **TODOs (Next Steps)**

### **1. Chunking Algorithm**
- Implement text → chunk splitting (sentence‑based or token‑based).
- Add overlap logic (e.g., 20–30% overlap).
- Integrate into ingestion pipeline.

### **2. SQLAlchemy Models**
Create models for:
- meetings  
- documents  
- chunks  
- tasks  
- events  
- threads  
- messages  

Then generate migrations with Alembic.

### **3. Ingestion Endpoint**
`POST /ingest/meeting`  
- Validate payload  
- Insert meeting + document  
- Chunk text  
- Embed chunks  
- Store chunks in Postgres + Chroma  

### **4. Intent Classifier**
Lightweight rule‑based classifier:
- Structured queries → SQL  
- Semantic queries → RAG  

Examples:
- “tasks due this week” → structured  
- “what did we decide about onboarding” → semantic  

### **5. Retrieval Filters**
Add metadata filters:
- date range  
- meeting category  
- participants  
- document purpose  

### **6. Thread + Message Memory**
Implement:
- create thread  
- append message  
- load last N messages  
- integrate into `/query`  

### **7. Confidence Layer**
- Compute avg/min/max similarity  
- If below threshold → return “not confident” JSON  
- Add to metadata  

### **8. Docker Integration**
- Build Dockerfile for API  
- Finalize docker‑compose  
- Test service startup order  
- Verify persistence volumes  

### **9. Health Check Endpoint**
`GET /health`  
- Check Postgres connection  
- Check Chroma connection  
- Check Ollama availability  

---

# 🔵 **Project State Summary**

You’ve built the **entire LLM + vector store foundation**, which is the hardest conceptual part. You now have:

- A deterministic JSON contract  
- A working LLM pipeline  
- A working embedding + vector retrieval pipeline  
- A clean module structure  
- A clear API design  
- A fully local, free, privacy‑preserving architecture  

What remains is mostly **plumbing**:

- Chunking  
- SQL models  
- Ingestion endpoint  
- Intent detection  
- Thread memory  
- Dockerization  

You’re past the “thinking” phase — now it’s just implementation.

---

If you want, I can generate:

- The chunking module  
- The SQLAlchemy models  
- The ingestion endpoint  
- The intent classifier  
- The full `/query` endpoint with threads + memory  
- The Dockerfile and docker‑compose walkthrough  

Just tell me which piece you want to build next.
