-- ClaWin1Click - Database Schema
-- PostgreSQL 16+
-- Single-platform (NOT multi-tenant)

-- ============================================
-- EXTENSIONS
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TRIGGER FUNCTIONS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Normalize text for memory deduplication
CREATE OR REPLACE FUNCTION normalize_text(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            TRANSLATE(
                input_text,
                'áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ',
                'aaaaaeeeeiiiioooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCN'
            ),
            '[^a-zA-Z0-9\s]', '', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Auto-normalize memory facts
CREATE OR REPLACE FUNCTION auto_normalize_fato()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fato_normalizado = normalize_text(NEW.fato);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- USERS (core)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255),  -- NULL for OAuth-only users
    nome VARCHAR(255),
    role VARCHAR(20) DEFAULT 'lead' CHECK (role IN ('admin', 'affiliate', 'subscriber', 'lead')),
    ref_code VARCHAR(50),  -- affiliate slug that referred this user
    stripe_customer_id VARCHAR(100),
    oauth_provider VARCHAR(20),  -- 'google', 'github', NULL
    oauth_id VARCHAR(255),
    profile_photo_url TEXT,
    language VARCHAR(5) DEFAULT 'pt',
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_stripe ON users(stripe_customer_id);


-- ============================================
-- USER PROFILES (extended info)
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    nome VARCHAR(255),
    telefone VARCHAR(20),
    cidade VARCHAR(100),
    pais VARCHAR(50) DEFAULT 'Brasil',
    language VARCHAR(5) DEFAULT 'pt',
    tom_preferido VARCHAR(50) DEFAULT 'friendly',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- CONVERSATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resumo VARCHAR(255),
    is_archived BOOLEAN DEFAULT FALSE,
    channel VARCHAR(20) DEFAULT 'web',  -- web, whatsapp, telegram
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    followup_date TIMESTAMPTZ,
    followup_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_followup ON conversations(followup_date)
    WHERE followup_date IS NOT NULL AND is_archived = FALSE;


-- ============================================
-- MESSAGES
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'admin', 'system')),
    content_encrypted BYTEA,  -- Fernet encrypted
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);


-- ============================================
-- USER MEMORIES
-- ============================================
CREATE TABLE IF NOT EXISTS user_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    categoria VARCHAR(30) NOT NULL CHECK (categoria IN (
        'IDENTITY', 'SUBSCRIPTION', 'INSTANCE', 'PREFERENCE',
        'SUPPORT', 'USAGE', 'BILLING', 'EVENT'
    )),
    fato TEXT NOT NULL,
    fato_normalizado TEXT,  -- auto-normalized for dedup
    importancia DECIMAL(3,2) DEFAULT 0.50,
    confianca DECIMAL(3,2) DEFAULT 0.80,
    source VARCHAR(20) DEFAULT 'extraction',
    mentions INTEGER DEFAULT 1,
    is_pinned BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'deleted')),
    superseded_by UUID REFERENCES user_memories(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_user_memories_updated_at BEFORE UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_user_memories_normalize BEFORE INSERT OR UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION auto_normalize_fato();

CREATE INDEX idx_user_memories_user ON user_memories(user_id);
CREATE INDEX idx_user_memories_categoria ON user_memories(user_id, categoria);
CREATE INDEX idx_user_memories_status ON user_memories(user_id, status);


-- ============================================
-- SUBSCRIPTIONS (Stripe)
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(100) UNIQUE,
    stripe_customer_id VARCHAR(100),
    plan VARCHAR(20) DEFAULT 'standard',
    status VARCHAR(20) DEFAULT 'incomplete' CHECK (status IN (
        'active', 'past_due', 'cancelled', 'incomplete', 'trialing'
    )),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);


-- ============================================
-- INSTANCES (OpenClaw deploys)
-- ============================================
CREATE TABLE IF NOT EXISTS instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    server_ip VARCHAR(45),
    hostname VARCHAR(100),
    status VARCHAR(20) DEFAULT 'provisioning' CHECK (status IN (
        'provisioning', 'active', 'suspended', 'terminated', 'error'
    )),
    openclaw_version VARCHAR(20),
    ai_provider VARCHAR(20),  -- anthropic, openai, google, deepseek
    ai_model VARCHAR(50),     -- claude-opus-4-6, gpt-5.2, gemini-3.0-flash
    ai_api_key_encrypted BYTEA,        -- CRITICAL: always encrypted
    telegram_bot_token_encrypted BYTEA, -- CRITICAL: always encrypted
    channel VARCHAR(20) DEFAULT 'telegram',  -- telegram, discord, whatsapp
    config JSONB DEFAULT '{}',
    last_heartbeat TIMESTAMPTZ,
    hostinger_vm_id BIGINT,
    hostinger_datacenter VARCHAR(20),
    hostinger_docker_project VARCHAR(100),
    provision_started_at TIMESTAMPTZ,
    provision_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_instances_updated_at BEFORE UPDATE ON instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_instances_user ON instances(user_id);
CREATE INDEX idx_instances_status ON instances(status);
CREATE INDEX idx_instances_subscription ON instances(subscription_id);
CREATE INDEX idx_instances_hostinger_vm ON instances(hostinger_vm_id)
    WHERE hostinger_vm_id IS NOT NULL;


-- ============================================
-- DEPLOYMENTS (instance lifecycle log)
-- ============================================
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id UUID REFERENCES instances(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN (
        'create', 'restart', 'update', 'suspend', 'terminate'
    )),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'completed', 'failed'
    )),
    error_log TEXT,
    external_action_id BIGINT,
    external_provider VARCHAR(20),  -- hostinger
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_deployments_instance ON deployments(instance_id, created_at DESC);


-- ============================================
-- AFFILIATES
-- ============================================
CREATE TABLE IF NOT EXISTS affiliates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    slug VARCHAR(50) UNIQUE NOT NULL,
    commission_rate DECIMAL(5,4) DEFAULT 0.2000,  -- 20%
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'banned')),
    total_earned DECIMAL(12,2) DEFAULT 0.00,
    total_paid DECIMAL(12,2) DEFAULT 0.00,
    payout_method VARCHAR(20),  -- pix, paypal, bank_transfer, crypto
    payout_details_encrypted BYTEA,  -- CRITICAL: always encrypted
    wallet_address_encrypted BYTEA,  -- Crypto wallet (USDT/USDC) — always encrypted
    wallet_network VARCHAR(20),  -- trc20, erc20, polygon, bep20
    auto_payout_enabled BOOLEAN DEFAULT FALSE,
    auto_payout_threshold DECIMAL(12,2) DEFAULT 25.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_affiliates_updated_at BEFORE UPDATE ON affiliates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_affiliates_slug ON affiliates(slug);
CREATE INDEX idx_affiliates_status ON affiliates(status);


-- ============================================
-- REFERRALS (affiliate -> referred user)
-- ============================================
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    affiliate_id UUID REFERENCES affiliates(id) ON DELETE CASCADE,
    referred_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'cancelled')),
    commission_amount DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_referrals_affiliate ON referrals(affiliate_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_user_id);


-- ============================================
-- AFFILIATE PAYOUTS
-- ============================================
CREATE TABLE IF NOT EXISTS affiliate_payouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    affiliate_id UUID REFERENCES affiliates(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    method VARCHAR(20),  -- pix, paypal, bank_transfer, crypto
    reference VARCHAR(100),  -- transaction ID
    tx_hash VARCHAR(100),  -- Blockchain transaction hash
    network VARCHAR(20),  -- trc20, erc20, polygon, bep20
    token VARCHAR(10),  -- USDT, USDC
    failure_reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'completed', 'failed'
    )),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_affiliate_payouts_affiliate ON affiliate_payouts(affiliate_id);


-- ============================================
-- AUDIT LOG
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action);


-- ============================================
-- PASSWORD RESET TOKENS
-- ============================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- PSYCHOLOGICAL PROFILE (communication style)
-- ============================================
CREATE TABLE IF NOT EXISTS user_psychological_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    communication_style VARCHAR(30) DEFAULT 'DIRECT',
    processing_style VARCHAR(30) DEFAULT 'PRACTICAL',
    preferred_response_length VARCHAR(20) DEFAULT 'BRIEF',
    emotional_baseline VARCHAR(20) DEFAULT 'NEUTRAL',
    interaction_count INTEGER DEFAULT 0,
    last_analysis TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_psych_updated_at BEFORE UPDATE ON user_psychological_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- LEARNING INTERACTIONS
-- ============================================
CREATE TABLE IF NOT EXISTS learning_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    strategy_used VARCHAR(30),
    feedback_type VARCHAR(30),
    feedback_score DECIMAL(3,2),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_user ON learning_interactions(user_id, created_at DESC);


-- ============================================
-- FOLLOWUPS (proactive follow-up queue)
-- ============================================
CREATE TABLE IF NOT EXISTS followups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    channel VARCHAR(20) DEFAULT 'telegram',  -- telegram, web
    status VARCHAR(20) DEFAULT 'suggested' CHECK (status IN (
        'suggested', 'approved', 'sent', 'cancelled', 'failed'
    )),
    scheduled_for TIMESTAMPTZ NOT NULL,
    message_draft TEXT NOT NULL,             -- AI-generated draft (editable)
    followup_note TEXT,                      -- internal context (never sent)
    lead_temperature VARCHAR(10) DEFAULT 'warm' CHECK (lead_temperature IN ('hot', 'warm', 'cold')),
    created_by VARCHAR(20) DEFAULT 'ai' CHECK (created_by IN ('ai', 'admin')),
    attempt_count INTEGER DEFAULT 0,
    sent_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER tr_followups_updated_at BEFORE UPDATE ON followups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE INDEX idx_followups_user ON followups(user_id);
CREATE INDEX idx_followups_status ON followups(status, scheduled_for)
    WHERE status = 'approved';
CREATE INDEX idx_followups_conversation ON followups(conversation_id)
    WHERE conversation_id IS NOT NULL;

-- Add opt-out / cooldown fields to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS followup_opt_out BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS followup_cooldown_until TIMESTAMPTZ;


-- ============================================
-- SEED DATA
-- ============================================

-- Admin user (change password after first login)
INSERT INTO users (id, email, senha_hash, nome, role, language)
VALUES (
    uuid_generate_v4(),
    'admin@clawin1click.com',
    -- bcrypt hash of 'admin123' (CHANGE IN PRODUCTION!)
    '$2b$12$LJ3m4ys3Lp9TZJKR8CxJNeF9V.I80OfGKFDR2bWYtYb8/VQ6S6dHi',
    'ClaWin Admin',
    'admin',
    'pt'
) ON CONFLICT (email) DO NOTHING;
