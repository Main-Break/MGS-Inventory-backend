-- Schema completo do banco (SQLite), num arquivo só, para consulta.
--
-- Quem cria as tabelas de verdade é database.py, com CREATE TABLE IF NOT
-- EXISTS rodado sozinho toda vez que o App sobe (ver main.py). Ao mudar o
-- schema em database.py, atualize este arquivo junto.

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'funcionario',
    active INTEGER NOT NULL DEFAULT 1
);

-- Catálogo do estoque. O label é o nome exato da classe que o modelo de IA
-- devolve, e é por ele que a contagem da foto acha o item cadastrado.
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0
);

-- Uma verificação = uma foto contada pela IA. detections guarda o resultado
-- (lista de label/count/confidence) como JSON. approved é do gestor e fica
-- nulo até alguém revisar.
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_id INTEGER REFERENCES items(id),
    photo_filename TEXT NOT NULL,
    detections TEXT NOT NULL,
    approved INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
