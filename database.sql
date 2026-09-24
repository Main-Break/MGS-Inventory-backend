-- Schema completo do banco, num arquivo só.
--
-- Este arquivo é só para consulta. Quem cria e atualiza as tabelas de
-- verdade é o migrations.py, que roda sozinho toda vez que o App sobe.
-- Ao acrescentar uma migração nova lá, atualize este arquivo junto, para
-- ele continuar mostrando o estado atual completo do banco.
--
-- A sintaxe abaixo é a do MySQL/MariaDB. No SQLite a única diferença que o
-- migrador aplica sozinho é a coluna id, que vira
-- "INTEGER PRIMARY KEY AUTOINCREMENT".

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('gestor', 'funcionario')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Catálogo do estoque. O label é o nome exato da classe que o modelo
-- devolve, e é por ele que a contagem da foto acha o item cadastrado.
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Uma verificação = uma contagem feita por alguém, com 1 ou mais fotos.
-- expected_item_id é o item que o funcionário selecionou antes de fotografar,
-- manual_count é a recontagem que ele informa depois, e approved é do gestor
-- (fica nulo até alguém revisar, já que revisar é opcional).
CREATE TABLE verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    expected_item_id INT NULL REFERENCES items(id),
    manual_count INT NULL,
    approved BOOLEAN NULL,
    approved_by INT NULL REFERENCES users(id),
    approved_at DATETIME NULL,
    approval_note VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE verification_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    verification_id INT NOT NULL REFERENCES verifications(id),
    image_filename VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Uma linha por classe detectada, somando o que apareceu em todas as fotos
-- da verificação. item_id fica nulo quando o label detectado não bate com
-- nenhum item cadastrado. avg_confidence é a confiança média (0 a 1) que o
-- próprio modelo reportou.
CREATE TABLE verification_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    verification_id INT NOT NULL REFERENCES verifications(id),
    item_id INT NULL REFERENCES items(id),
    label VARCHAR(100) NOT NULL,
    count INT NOT NULL,
    avg_confidence FLOAT NOT NULL
);

-- Controle interno do migrador (não mexer na mão).
CREATE TABLE schema_migrations (
    version INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
