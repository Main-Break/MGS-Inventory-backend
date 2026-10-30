-- ============================================================================
-- Esquema completo do banco de dados (MySQL / MariaDB).
--
-- Este arquivo é a fonte oficial das tabelas e deve refletir sempre o estado
-- atual do banco. Toda alteração de tabela é feita aqui e aplicada à mão.
--
-- Como aplicar:
--     mariadb -u USUARIO -p NOME_DO_BANCO < database/database.sql
--
-- Padrões usados em todas as tabelas:
--     id          UUID-4 (CHAR(36)), gerado pela classe Database no insert.
--     status      'active' (ativo), 'disable' (desativado) ou 'deleted' (apagado, soft delete).
--     created_at  data e hora em que o registro foi criado.
--     updated_at  data e hora da última alteração (atualizada sozinha pelo banco).
-- ============================================================================


-- ----------------------------------------------------------------------------
-- users: pessoas que acessam o sistema.
--     role 'gestor'      pode cadastrar usuários e itens e aprovar verificações.
--     role 'funcionario' tira as fotos e vê apenas as próprias verificações.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              CHAR(36)        NOT NULL,
    name            VARCHAR(255)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            ENUM('gestor', 'funcionario')         NOT NULL DEFAULT 'funcionario',
    status          ENUM('active', 'disable', 'deleted')  NOT NULL DEFAULT 'active',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- user_permissions: permissões extras liberadas pelo gestor para um usuário.
--     O gestor sempre pode tudo, então esta tabela só é usada para funcionários.
--     permission é uma das chaves listadas em models/permissions.py
--     (ex: 'itens.create', 'materials.edit'). Fica como texto, e não ENUM,
--     para que uma permissão nova não exija alterar a tabela.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_permissions (
    id              CHAR(36)        NOT NULL,
    user_id         CHAR(36)        NOT NULL,
    permission      VARCHAR(50)     NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_user_permissions (user_id, permission),
    CONSTRAINT fk_user_permissions_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- materials: materiais de que os itens são feitos (PEAD, PP, POM, Nylon...).
--     density é o peso específico do material em g/cm³ e é usado nas
--     equações de peso e quantidade dos itens.
--     Fica em tabela própria para que um material novo ou uma densidade
--     corrigida seja cadastrada pelo sistema, sem alterar código.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id              CHAR(36)        NOT NULL,
    code            VARCHAR(20)     NOT NULL,               -- sigla (PEAD, PP, POM, NYLON...)
    name            VARCHAR(100)    NOT NULL,               -- nome completo (Polietileno de alta densidade)
    density         DECIMAL(6,3)    NOT NULL,               -- peso específico em g/cm³
    description     TEXT            NULL,                   -- observações sobre o material
    status          ENUM('active', 'disable', 'deleted')  NOT NULL DEFAULT 'active',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_materials_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- itens: itens do estoque que são conferidos pelas fotos.
--     Não é cadastro de venda, é o cadastro usado para a verificação de estoque.
--     label é o nome exato da classe que o modelo de IA (YOLO) devolve ao
--     reconhecer o item na foto, por isso é obrigatório e único.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS itens (
    id              CHAR(36)        NOT NULL,

    -- Identificação
    name            VARCHAR(255)    NOT NULL,               -- nome do item
    description     TEXT            NULL,                   -- descrição detalhada
    label           VARCHAR(100)    NOT NULL,               -- classe que a IA devolve
    sku             VARCHAR(100)    NULL,                   -- código interno do item
    barcode         VARCHAR(50)     NULL,                   -- código de barras (EAN, GTIN...)
    brand           VARCHAR(100)    NULL,                   -- marca ou fabricante
    category        VARCHAR(100)    NULL,                   -- categoria ou grupo do item
    material_id     CHAR(36)        NULL,                   -- material de que o item é feito

    -- Medidas físicas
    unit            VARCHAR(20)     NOT NULL DEFAULT 'un',  -- unidade de contagem (un, cx, pct, kg...)
    weight_kg       DECIMAL(10,3)   NULL,                   -- peso em quilos
    height_cm       DECIMAL(10,2)   NULL,                   -- altura em centímetros
    width_cm        DECIMAL(10,2)   NULL,                   -- largura em centímetros
    length_cm       DECIMAL(10,2)   NULL,                   -- comprimento em centímetros

    -- Estoque
    stock_quantity  INT             NOT NULL DEFAULT 0,     -- quantidade atual
    min_stock       INT             NOT NULL DEFAULT 0,     -- quantidade mínima desejada
    location        VARCHAR(100)    NULL,                   -- onde fica guardado (galpão, prateleira...)

    status          ENUM('active', 'disable', 'deleted')  NOT NULL DEFAULT 'active',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_itens_label (label),
    UNIQUE KEY uk_itens_sku (sku),
    UNIQUE KEY uk_itens_barcode (barcode),
    CONSTRAINT fk_itens_material FOREIGN KEY (material_id) REFERENCES materials (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- verifications: cada foto enviada para conferência.
--     detections guarda o resultado da IA em JSON, uma lista de
--     {"label": ..., "count": ..., "confidence": ...}.
--     approved fica NULL até um gestor aprovar (1) ou reprovar (0).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verifications (
    id              CHAR(36)        NOT NULL,
    user_id         CHAR(36)        NOT NULL,               -- quem tirou a foto
    item_id         CHAR(36)        NULL,                   -- item conferido (opcional)
    photo_filename  VARCHAR(255)    NOT NULL,               -- nome do arquivo em data/upload/
    detections      JSON            NOT NULL,
    approved        TINYINT(1)      NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_verifications_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_verifications_item FOREIGN KEY (item_id) REFERENCES itens (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
