-- Inicializar base de datos para Dyzen
-- Sistema de compartición de imágenes con compresión adaptativa
-- Desarrollado por Grupo 1 - SCM

-- Eliminar tablas existentes si existen
DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS network_metrics;
DROP TABLE IF EXISTS users;

-- Tabla de usuarios (básica)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    karma INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1
);

-- Tabla principal de posts
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    image_path TEXT NOT NULL,
    compressed_path TEXT,
    original_size INTEGER NOT NULL,
    compressed_size INTEGER,
    compression_level INTEGER DEFAULT 16 CHECK (compression_level IN (8, 16, 32)),
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    username TEXT DEFAULT 'Anonymous',
    subreddit TEXT DEFAULT 'pics',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_enhanced BOOLEAN DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    metadata TEXT -- JSON con información adicional
);

-- Tabla de comentarios
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    parent_comment_id INTEGER, -- Para respuestas anidadas
    username TEXT DEFAULT 'Anonymous',
    content TEXT NOT NULL,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES comments (id) ON DELETE CASCADE
);

-- Tabla de votos
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    comment_id INTEGER,
    user_ip TEXT NOT NULL, -- En producción usar user_id
    vote_type TEXT NOT NULL CHECK (vote_type IN ('up', 'down')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_ip, comment_id), -- Prevenir votos duplicados
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE CASCADE
);

-- Tabla de métricas de red
CREATE TABLE network_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_ip TEXT,
    bandwidth REAL NOT NULL,
    latency REAL NOT NULL,
    quality TEXT NOT NULL CHECK (quality IN ('poor', 'medium', 'good')),
    recommended_compression INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de estadísticas de uso
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE DEFAULT (date('now')),
    images_uploaded INTEGER DEFAULT 0,
    images_enhanced INTEGER DEFAULT 0,
    total_compression_saved INTEGER DEFAULT 0,
    avg_compression_ratio REAL DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_score ON posts((upvotes - downvotes) DESC);
CREATE INDEX idx_posts_subreddit ON posts(subreddit);
CREATE INDEX idx_posts_username ON posts(username);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);
CREATE INDEX idx_votes_post_id ON votes(post_id);
CREATE INDEX idx_votes_comment_id ON votes(comment_id);
CREATE INDEX idx_votes_user_ip ON votes(user_ip);
CREATE INDEX idx_network_metrics_timestamp ON network_metrics(timestamp);

-- Triggers para mantener contadores actualizados
CREATE TRIGGER update_post_votes_after_vote_insert
AFTER INSERT ON votes
WHEN NEW.post_id IS NOT NULL
BEGIN
    UPDATE posts SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE post_id = NEW.post_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE post_id = NEW.post_id AND vote_type = 'down')
    WHERE id = NEW.post_id;
END;

CREATE TRIGGER update_post_votes_after_vote_update
AFTER UPDATE ON votes
WHEN NEW.post_id IS NOT NULL
BEGIN
    UPDATE posts SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE post_id = NEW.post_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE post_id = NEW.post_id AND vote_type = 'down')
    WHERE id = NEW.post_id;
END;

CREATE TRIGGER update_post_votes_after_vote_delete
AFTER DELETE ON votes
WHEN OLD.post_id IS NOT NULL
BEGIN
    UPDATE posts SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE post_id = OLD.post_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE post_id = OLD.post_id AND vote_type = 'down')
    WHERE id = OLD.post_id;
END;

-- Triggers similares para comentarios
CREATE TRIGGER update_comment_votes_after_vote_insert
AFTER INSERT ON votes
WHEN NEW.comment_id IS NOT NULL
BEGIN
    UPDATE comments SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = NEW.comment_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = NEW.comment_id AND vote_type = 'down')
    WHERE id = NEW.comment_id;
END;

CREATE TRIGGER update_comment_votes_after_vote_update
AFTER UPDATE ON votes
WHEN NEW.comment_id IS NOT NULL
BEGIN
    UPDATE comments SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = NEW.comment_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = NEW.comment_id AND vote_type = 'down')
    WHERE id = NEW.comment_id;
END;

CREATE TRIGGER update_comment_votes_after_vote_delete
AFTER DELETE ON votes
WHEN OLD.comment_id IS NOT NULL
BEGIN
    UPDATE comments SET 
        upvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = OLD.comment_id AND vote_type = 'up'),
        downvotes = (SELECT COUNT(*) FROM votes WHERE comment_id = OLD.comment_id AND vote_type = 'down')
    WHERE id = OLD.comment_id;
END;

-- Insertar datos de ejemplo
INSERT INTO users (username, email, karma) VALUES
('admin', 'admin@imagereddit.com', 1000),
('photographer_pro', 'photo@example.com', 500),
('nature_lover', 'nature@example.com', 300),
('tech_enthusiast', 'tech@example.com', 250);

INSERT INTO posts (title, image_path, compressed_path, original_size, compressed_size, compression_level, upvotes, downvotes, username, subreddit) VALUES
('Hermoso atardecer en la montaña', 'static/uploads/sunset.jpg', 'static/uploads/sunset_compressed_16.jpg', 2048000, 512000, 16, 45, 3, 'photographer_pro', 'pics'),
('Mi gato durmiendo', 'static/uploads/cat.jpg', 'static/uploads/cat_compressed_8.jpg', 1536000, 384000, 8, 32, 1, 'nature_lover', 'aww'),
('Nueva cámara que compré', 'static/uploads/camera.jpg', 'static/uploads/camera_compressed_32.jpg', 3072000, 1536000, 32, 28, 2, 'tech_enthusiast', 'photography'),
('Paisaje urbano nocturno', 'static/uploads/city.jpg', 'static/uploads/city_compressed_16.jpg', 2560000, 640000, 16, 67, 4, 'photographer_pro', 'pics'),
('Experimento con macro fotografía', 'static/uploads/macro.jpg', 'static/uploads/macro_compressed_32.jpg', 4096000, 2048000, 32, 23, 1, 'nature_lover', 'photography');

INSERT INTO comments (post_id, username, content, upvotes, downvotes) VALUES
(1, 'nature_lover', '¡Increíble foto! ¿Qué cámara usaste?', 12, 0),
(1, 'photographer_pro', 'Gracias! Usé una Canon EOS R5 con lente 24-70mm', 8, 0),
(1, 'tech_enthusiast', 'La compresión se ve muy bien, apenas se nota la diferencia', 5, 0),
(2, 'photographer_pro', 'Qué tierno! Los gatos siempre dan las mejores fotos', 15, 0),
(2, 'admin', 'Perfecto ejemplo de cuándo usar compresión alta para redes lentas', 3, 0),
(3, 'nature_lover', '¿Vale la pena la inversión? Estoy pensando en actualizar mi equipo', 7, 0),
(4, 'tech_enthusiast', 'El contraste nocturno quedó perfecto', 9, 1),
(5, 'admin', 'Excelente técnica macro, se ven todos los detalles', 6, 0);

INSERT INTO network_metrics (user_ip, bandwidth, latency, quality, recommended_compression) VALUES
('192.168.1.100', 85.5, 45, 'good', 32),
('192.168.1.101', 32.1, 120, 'medium', 16),
('192.168.1.102', 18.7, 180, 'poor', 8),
('192.168.1.103', 95.2, 35, 'good', 32),
('192.168.1.104', 28.9, 95, 'medium', 16);

INSERT INTO usage_stats (date, images_uploaded, images_enhanced, total_compression_saved, avg_compression_ratio, unique_visitors) VALUES
('2024-01-15', 25, 18, 15728640, 68.5, 150),
('2024-01-14', 32, 24, 20971520, 72.3, 180),
('2024-01-13', 19, 15, 12582912, 65.8, 120),
('2024-01-12', 28, 20, 18874368, 70.1, 165),
('2024-01-11', 35, 28, 25165824, 74.2, 200);

-- Vistas útiles para estadísticas
CREATE VIEW post_stats AS
SELECT 
    p.id,
    p.title,
    p.username,
    p.subreddit,
    p.upvotes,
    p.downvotes,
    (p.upvotes - p.downvotes) as score,
    p.compression_level,
    ROUND((1.0 - CAST(p.compressed_size AS REAL) / p.original_size) * 100, 1) as compression_ratio,
    COUNT(c.id) as comment_count,
    p.created_at
FROM posts p
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY p.id;

CREATE VIEW top_posts AS
SELECT *
FROM post_stats
ORDER BY score DESC, created_at DESC;

CREATE VIEW compression_efficiency AS
SELECT 
    compression_level,
    COUNT(*) as post_count,
    AVG(compression_ratio) as avg_compression_ratio,
    AVG(upvotes - downvotes) as avg_score
FROM post_stats
GROUP BY compression_level;

-- Función para limpiar datos antiguos (simulada con DELETE)
-- En producción, esto sería un procedimiento almacenado o tarea programada

PRAGMA foreign_keys = ON;

-- Mensaje de confirmación
SELECT 'Base de datos Dyzen inicializada correctamente' as status,
       (SELECT COUNT(*) FROM posts) as posts_count,
       (SELECT COUNT(*) FROM comments) as comments_count,
       (SELECT COUNT(*) FROM votes) as votes_count;
