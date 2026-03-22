-- TODO: config to match ~/requirements.txt

CREATE TABLE meetings (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    purpose         TEXT,
    participants    TEXT[],          -- email preferred; TODO: format email ONLY or default firstName.lastName
    platform        TEXT,            -- Zoom, Teams, phone, IRL, other
    category        TEXT,            -- academic, professional, collegiate, other
    meeting_time    TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    meeting_id      INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    purpose         TEXT,            -- SOP, meeting notes, rules, status, other
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks are referenced here, but embeddings live in Chroma
CREATE TABLE chunks (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text      TEXT NOT NULL,
    position        INTEGER NOT NULL,
    metadata        JSONB DEFAULT '{}'::JSONB, -- TODO: ensure type safety of JSONB
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tasks (
    id              SERIAL PRIMARY KEY,
    meeting_id      INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    description     TEXT NOT NULL,
    owners          TEXT[],          -- or JSONB
    due_date        DATE,
    status          TEXT CHECK (status IN ('done','in_progress','unseen','opened')) DEFAULT 'unseen',
    cmr             TEXT,            -- whatever CMR means for you (notes, context, etc.)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE events (
    id              SERIAL PRIMARY KEY,
    related_task_ids INTEGER[],      -- or a join table if you want many-to-many
    event_date      DATE,
    deadline        DATE,
    status          TEXT,            -- complete, cancelled, unplanned, planned, etc.
    metadata        JSONB DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE threads (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    is_open         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
    id              SERIAL PRIMARY KEY,
    thread_id       INTEGER REFERENCES threads(id) ON DELETE CASCADE,
    role            TEXT CHECK (role IN ('user','assistant','system')) NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);