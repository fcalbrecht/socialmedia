-- ============================================================
-- Schema PostgreSQL: @cadeiaparamaustratossp
-- Executar uma vez para criar o banco de dados.
-- Uso: psql -d socialmedia -f tools/db/schema.sql
-- ============================================================

-- Tabela de ideias de conteúdo
CREATE TABLE IF NOT EXISTS content_ideas (
    id SERIAL PRIMARY KEY,
    tema TEXT NOT NULL,
    formato VARCHAR(20) CHECK (formato IN ('estatico', 'carrossel', 'reel')),
    fonte VARCHAR(50),
    score_potencial INTEGER CHECK (score_potencial BETWEEN 0 AND 100),
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovado', 'descartado', 'publicado')),
    notas TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de posts publicados
CREATE TABLE IF NOT EXISTS published_posts (
    id SERIAL PRIMARY KEY,
    instagram_post_id VARCHAR(100),
    content_idea_id INTEGER REFERENCES content_ideas(id),
    tipo VARCHAR(20) CHECK (tipo IN ('estatico', 'carrossel', 'reel')),
    legenda TEXT,
    hashtags TEXT[],
    data_publicacao TIMESTAMP,
    horario TIME,
    tema TEXT,
    score_potencial INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de métricas por post
CREATE TABLE IF NOT EXISTS post_metrics (
    id SERIAL PRIMARY KEY,
    published_post_id INTEGER REFERENCES published_posts(id),
    medicao VARCHAR(10) CHECK (medicao IN ('24h', '48h', '7d')),
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    profile_visits INTEGER DEFAULT 0,
    follows_from_post INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (published_post_id, medicao)
);

-- Tabela de hashtags com performance histórica
CREATE TABLE IF NOT EXISTS hashtags (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(100) UNIQUE NOT NULL,
    vezes_usada INTEGER DEFAULT 0,
    media_engagement DECIMAL(5,2) DEFAULT 0,
    categoria VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para consultas frequentes
CREATE INDEX IF NOT EXISTS idx_content_ideas_status ON content_ideas(status);
CREATE INDEX IF NOT EXISTS idx_content_ideas_formato ON content_ideas(formato);
CREATE INDEX IF NOT EXISTS idx_published_posts_data ON published_posts(data_publicacao);
CREATE INDEX IF NOT EXISTS idx_post_metrics_post_id ON post_metrics(published_post_id);
CREATE INDEX IF NOT EXISTS idx_hashtags_engagement ON hashtags(media_engagement DESC);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_content_ideas_updated_at
    BEFORE UPDATE ON content_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_hashtags_updated_at
    BEFORE UPDATE ON hashtags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
