-- Esquema de Base de Datos para N8NMC API
-- Diseñado para almacenar análisis de dominios, URLs y keywords

-- Tabla principal de dominios
CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL UNIQUE,
    sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de análisis de dominios (resúmenes)
CREATE TABLE IF NOT EXISTS domain_analyses (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_urls INTEGER NOT NULL,
    urls_processed INTEGER NOT NULL,
    processing_time_seconds DECIMAL(10,2),
    page_types JSONB, -- {"blog": 8, "mixto": 2}
    audiences JSONB, -- {"gaming": 10, "B2B": 2}
    intents JSONB, -- {"informacional": 8, "comercial": 2}
    top_keywords_client JSONB,
    top_keywords_product JSONB,
    top_keywords_general JSONB,
    summary_stats JSONB,
    raw_data JSONB, -- Datos completos del JSON original
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de URLs analizadas
CREATE TABLE IF NOT EXISTS analyzed_urls (
    id SERIAL PRIMARY KEY,
    domain_analysis_id INTEGER REFERENCES domain_analyses(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL, -- Hash para evitar duplicados
    page_type VARCHAR(50),
    audiences TEXT[], -- Array de audiencias
    intent VARCHAR(50),
    word_count INTEGER,
    heading_count INTEGER,
    processing_time_seconds DECIMAL(10,2),
    title TEXT,
    description TEXT,
    main_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain_analysis_id, url_hash)
);

-- Tabla de keywords extraídas
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES analyzed_urls(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    score DECIMAL(8,6) NOT NULL,
    bucket VARCHAR(50) NOT NULL, -- cliente, producto_o_post, generales_seo
    source VARCHAR(50), -- yake, keybert, combined
    position INTEGER, -- Posición en el ranking
    contextual_score DECIMAL(8,6),
    relevance_score DECIMAL(8,6),
    position_score DECIMAL(8,6),
    frequency_score DECIMAL(8,6),
    sector_boost DECIMAL(8,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de estadísticas agregadas por dominio
CREATE TABLE IF NOT EXISTS domain_stats (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    stat_date DATE DEFAULT CURRENT_DATE,
    total_keywords INTEGER,
    avg_keywords_per_url DECIMAL(8,2),
    bucket_distribution JSONB, -- Distribución por buckets
    sector_keywords JSONB, -- Keywords específicas del sector
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain_id, stat_date)
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_domains_domain_name ON domains(domain_name);
CREATE INDEX IF NOT EXISTS idx_domains_sector ON domains(sector);
CREATE INDEX IF NOT EXISTS idx_domain_analyses_domain_id ON domain_analyses(domain_id);
CREATE INDEX IF NOT EXISTS idx_domain_analyses_date ON domain_analyses(analysis_date);
CREATE INDEX IF NOT EXISTS idx_analyzed_urls_domain_analysis_id ON analyzed_urls(domain_analysis_id);
CREATE INDEX IF NOT EXISTS idx_analyzed_urls_url_hash ON analyzed_urls(url_hash);
CREATE INDEX IF NOT EXISTS idx_analyzed_urls_page_type ON analyzed_urls(page_type);
CREATE INDEX IF NOT EXISTS idx_keywords_url_id ON keywords(url_id);
CREATE INDEX IF NOT EXISTS idx_keywords_bucket ON keywords(bucket);
CREATE INDEX IF NOT EXISTS idx_keywords_score ON keywords(score DESC);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);

-- Índices GIN para búsquedas en JSONB
CREATE INDEX IF NOT EXISTS idx_domain_analyses_page_types_gin ON domain_analyses USING GIN(page_types);
CREATE INDEX IF NOT EXISTS idx_domain_analyses_audiences_gin ON domain_analyses USING GIN(audiences);
CREATE INDEX IF NOT EXISTS idx_domain_analyses_intents_gin ON domain_analyses USING GIN(intents);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_domains_updated_at BEFORE UPDATE ON domains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Vista para análisis completos con joins
CREATE OR REPLACE VIEW domain_analysis_summary AS
SELECT 
    d.id as domain_id,
    d.domain_name,
    d.sector,
    da.id as analysis_id,
    da.analysis_date,
    da.total_urls,
    da.urls_processed,
    da.processing_time_seconds,
    da.page_types,
    da.audiences,
    da.intents,
    COUNT(au.id) as urls_analyzed,
    AVG(au.word_count) as avg_word_count,
    COUNT(k.id) as total_keywords,
    AVG(k.score) as avg_keyword_score
FROM domains d
JOIN domain_analyses da ON d.id = da.domain_id
LEFT JOIN analyzed_urls au ON da.id = au.domain_analysis_id
LEFT JOIN keywords k ON au.id = k.url_id
GROUP BY d.id, d.domain_name, d.sector, da.id, da.analysis_date, 
         da.total_urls, da.urls_processed, da.processing_time_seconds,
         da.page_types, da.audiences, da.intents;

-- Vista para top keywords por dominio
CREATE OR REPLACE VIEW top_keywords_by_domain AS
SELECT 
    d.domain_name,
    d.sector,
    k.keyword,
    k.bucket,
    AVG(k.score) as avg_score,
    COUNT(k.id) as frequency,
    COUNT(DISTINCT au.id) as url_count
FROM domains d
JOIN domain_analyses da ON d.id = da.domain_id
JOIN analyzed_urls au ON da.id = au.domain_analysis_id
JOIN keywords k ON au.id = k.url_id
GROUP BY d.domain_name, d.sector, k.keyword, k.bucket
ORDER BY d.domain_name, avg_score DESC;

-- Comentarios en las tablas
COMMENT ON TABLE domains IS 'Dominios analizados por la API';
COMMENT ON TABLE domain_analyses IS 'Análisis completos de dominios con resúmenes';
COMMENT ON TABLE analyzed_urls IS 'URLs individuales analizadas';
COMMENT ON TABLE keywords IS 'Keywords extraídas con scores y clasificaciones';
COMMENT ON TABLE domain_stats IS 'Estadísticas agregadas por dominio y fecha';

COMMENT ON COLUMN domains.sector IS 'Sector detectado: legal, sports, technology, etc.';
COMMENT ON COLUMN domain_analyses.page_types IS 'Distribución de tipos de página en JSON';
COMMENT ON COLUMN domain_analyses.audiences IS 'Distribución de audiencias en JSON';
COMMENT ON COLUMN domain_analyses.intents IS 'Distribución de intenciones en JSON';
COMMENT ON COLUMN keywords.bucket IS 'Clasificación: cliente, producto_o_post, generales_seo';
COMMENT ON COLUMN keywords.score IS 'Score final de la keyword (0-1)';

