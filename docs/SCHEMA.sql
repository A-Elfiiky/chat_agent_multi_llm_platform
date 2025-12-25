-- Database Schema for Customer Service Platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table (Admins, Agents)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'agent', 'viewer')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- 2. Sessions Table (Chat Sessions)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('web', 'email', 'voice')),
    customer_id VARCHAR(255), -- Email or Phone
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'escalated')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

-- 3. Message Logs (Audit Trail & History)
CREATE TABLE message_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id),
    sender VARCHAR(50) NOT NULL CHECK (sender IN ('user', 'bot', 'agent')),
    content TEXT NOT NULL, -- Redacted content
    original_content TEXT, -- Encrypted original (optional)
    intent VARCHAR(100),
    sentiment_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. RAG Interaction Logs (Observability)
CREATE TABLE rag_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES message_logs(id),
    query_text TEXT,
    retrieved_doc_ids TEXT[], -- Array of FAQ IDs
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    latency_ms INTEGER,
    confidence_score FLOAT,
    is_fallback BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tickets (Escalations)
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id),
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved')),
    priority VARCHAR(20) DEFAULT 'medium',
    assigned_to UUID REFERENCES users(id),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. FAQ Metadata (Synced with Vector Store)
CREATE TABLE faq_documents (
    id VARCHAR(255) PRIMARY KEY, -- Matches Vector Store ID
    title TEXT NOT NULL,
    section VARCHAR(100),
    content_hash VARCHAR(64), -- For change detection
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. FAQ Records (GUI CRUD Source of Truth)
CREATE TABLE faqs (
    id VARCHAR(255) PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_faqs_category ON faqs(category);
CREATE INDEX idx_faqs_updated_at ON faqs(updated_at DESC);

-- 8. LLM API Test Results (Dashboard Health Module)
CREATE TABLE llm_test_results (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    api_key_present BOOLEAN NOT NULL,
    latency_ms INTEGER,
    response_sample TEXT,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_tests_provider ON llm_test_results(provider, created_at DESC);

-- 9. Telephony Test Logs (Twilio Tester)
CREATE TABLE telephony_test_logs (
    id SERIAL PRIMARY KEY,
    test_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    twilio_number VARCHAR(30),
    call_sid VARCHAR(64),
    latency_ms INTEGER,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telephony_tests_type ON telephony_test_logs(test_type, created_at DESC);

-- Indexes
CREATE INDEX idx_sessions_customer ON sessions(customer_id);
CREATE INDEX idx_messages_session ON message_logs(session_id);
CREATE INDEX idx_rag_logs_provider ON rag_logs(llm_provider);
