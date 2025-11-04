"""
Database schema initialization for the modern service architecture.
Creates all required tables for the application.
"""

import logging
from database import get_db_manager

logger = logging.getLogger(__name__)


def initialize_schema():
    """Initialize database tables if they don't exist."""
    logger.info("Initializing database schema...")
    
    db_manager = get_db_manager()
    
    create_tables_sql = """
    -- Create Usuarios table
    CREATE TABLE IF NOT EXISTS Usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        nivel VARCHAR(20) DEFAULT 'user',
        chat_id BIGINT
    );

    -- Create Produtos table
    CREATE TABLE IF NOT EXISTS Produtos (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        emoji VARCHAR(10),
        media_file_id VARCHAR(255)
    );

    -- Create Expeditions table (for pirate expeditions) - MUST BE BEFORE Vendas
    CREATE TABLE IF NOT EXISTS Expeditions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        owner_chat_id BIGINT NOT NULL,
        owner_user_id BIGINT,
        owner_key TEXT,
        admin_key TEXT,
        encryption_version INTEGER DEFAULT 1,
        anonymization_level VARCHAR(20) DEFAULT 'standard' CHECK (anonymization_level IN ('none', 'standard', 'enhanced', 'maximum')),
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
        deadline TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        description TEXT,
        target_completion_date TIMESTAMP,
        progress_notes TEXT
    );

    -- Create Vendas table
    CREATE TABLE IF NOT EXISTS Vendas (
        id SERIAL PRIMARY KEY,
        comprador VARCHAR(100) NOT NULL,
        data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE SET NULL
    );

    -- Create ItensVenda table
    CREATE TABLE IF NOT EXISTS ItensVenda (
        id SERIAL PRIMARY KEY,
        venda_id INTEGER REFERENCES Vendas(id) ON DELETE CASCADE,
        produto_id INTEGER REFERENCES Produtos(id),
        quantidade INTEGER NOT NULL,
        valor_unitario DECIMAL(10,2) NOT NULL,
        produto_nome VARCHAR(100) NOT NULL
    );

    -- Create Estoque table
    CREATE TABLE IF NOT EXISTS Estoque (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER REFERENCES Produtos(id) ON DELETE CASCADE,
        quantidade INTEGER NOT NULL,
        preco DECIMAL(10,2) NOT NULL,
        custo DECIMAL(10,2),
        data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        quantidade_restante INTEGER NOT NULL DEFAULT 0
    );

    -- Create Pagamentos table
    CREATE TABLE IF NOT EXISTS Pagamentos (
        id SERIAL PRIMARY KEY,
        venda_id INTEGER REFERENCES Vendas(id) ON DELETE CASCADE,
        valor_pago DECIMAL(10,2) NOT NULL,
        data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create SmartContracts table (for blockchain functionality)
    CREATE TABLE IF NOT EXISTS SmartContracts (
        id SERIAL PRIMARY KEY,
        codigo VARCHAR(100) UNIQUE NOT NULL,
        criador_chat_id BIGINT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT TRUE
    );

    -- Create Transacoes table (for smart contract transactions)
    CREATE TABLE IF NOT EXISTS Transacoes (
        id SERIAL PRIMARY KEY,
        contract_id INTEGER REFERENCES SmartContracts(id) ON DELETE CASCADE,
        descricao TEXT NOT NULL,
        chat_id BIGINT NOT NULL,
        data_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmado BOOLEAN DEFAULT FALSE
    );

    -- Create Configuracoes table (for app settings)
    CREATE TABLE IF NOT EXISTS Configuracoes (
        id SERIAL PRIMARY KEY,
        chave VARCHAR(100) UNIQUE NOT NULL,
        valor TEXT,
        descricao TEXT,
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create user_master_keys table (for consistent user encryption keys)
    CREATE TABLE IF NOT EXISTS user_master_keys (
        id SERIAL PRIMARY KEY,
        owner_chat_id BIGINT UNIQUE NOT NULL,
        master_key TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        key_version INTEGER DEFAULT 1
    );

    -- Create BroadcastMessages table (for broadcast messaging system)
    CREATE TABLE IF NOT EXISTS BroadcastMessages (
        id SERIAL PRIMARY KEY,
        sender_chat_id BIGINT NOT NULL,
        message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('text', 'html', 'markdown', 'poll', 'dice')),
        message_content TEXT NOT NULL,
        poll_question TEXT,
        poll_options JSON,
        dice_emoji VARCHAR(10),
        total_recipients INTEGER DEFAULT 0,
        successful_deliveries INTEGER DEFAULT 0,
        failed_deliveries INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        completed_at TIMESTAMP,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'completed', 'failed'))
    );

    -- Create PollAnswers table (for tracking poll responses)
    CREATE TABLE IF NOT EXISTS PollAnswers (
        id SERIAL PRIMARY KEY,
        broadcast_id INTEGER REFERENCES BroadcastMessages(id) ON DELETE CASCADE,
        poll_id VARCHAR(255) NOT NULL,
        user_id BIGINT NOT NULL,
        username VARCHAR(100),
        option_id INTEGER NOT NULL,
        option_text TEXT NOT NULL,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(poll_id, user_id)
    );

    -- Create CashBalance table (for revenue tracking)
    CREATE TABLE IF NOT EXISTS CashBalance (
        id SERIAL PRIMARY KEY,
        saldo_atual DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create CashTransactions table (for balance history)
    CREATE TABLE IF NOT EXISTS CashTransactions (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('receita', 'despesa', 'ajuste')),
        valor DECIMAL(10,2) NOT NULL,
        descricao TEXT,
        venda_id INTEGER REFERENCES Vendas(id),
        pagamento_id INTEGER REFERENCES Pagamentos(id),
        usuario_chat_id BIGINT,
        saldo_anterior DECIMAL(10,2) NOT NULL,
        saldo_novo DECIMAL(10,2) NOT NULL,
        data_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );


    -- Create expedition_items table (for expedition inventory requirements)
    -- SECURITY: Supports full encryption mode for item anonymization
    CREATE TABLE IF NOT EXISTS expedition_items (
        id SERIAL PRIMARY KEY,
        expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE CASCADE,
        produto_id INTEGER REFERENCES Produtos(id),
        original_product_name VARCHAR(200),  -- NULLABLE: NULL when using full encryption
        encrypted_product_name TEXT,
        encrypted_mapping TEXT,  -- AES-256-GCM encrypted original name
        anonymized_item_code VARCHAR(50),
        item_type VARCHAR(50) DEFAULT 'product',  -- product, custom, resource
        quantity_required INTEGER NOT NULL,
        quantity_consumed INTEGER DEFAULT 0,
        target_unit_price DECIMAL(10,2),
        actual_avg_price DECIMAL(10,2),
        item_status VARCHAR(20) DEFAULT 'active' CHECK (item_status IN ('active', 'completed', 'cancelled', 'suspended')),
        priority_level INTEGER DEFAULT 1 CHECK (priority_level BETWEEN 1 AND 5),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_chat_id BIGINT,
        UNIQUE(expedition_id, encrypted_product_name),
        CONSTRAINT unique_original_product_when_not_null UNIQUE NULLS NOT DISTINCT (expedition_id, original_product_name)
    );

    -- REMOVED: pirate_names table - replaced by expedition_pirates
    -- REMOVED: item_consumptions table - migrated to expedition_assignments + expedition_payments
    -- All consumption tracking now uses the assignment-based architecture

    -- Create item_mappings table (for global custom item/product names)
    CREATE TABLE IF NOT EXISTS item_mappings (
        id SERIAL PRIMARY KEY,
        product_name VARCHAR(100) NOT NULL UNIQUE,
        custom_name VARCHAR(200) NOT NULL,
        description TEXT,
        is_fantasy_generated BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_chat_id BIGINT,
        UNIQUE(custom_name)
    );

    -- Create expedition_pirates table (for managing expedition participants)
    -- SECURITY: original_name is NULLABLE to support full encryption mode
    -- When encrypted_identity is used, original_name MUST be NULL for true anonymization
    CREATE TABLE IF NOT EXISTS expedition_pirates (
        id SERIAL PRIMARY KEY,
        expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE CASCADE,
        pirate_name VARCHAR(100) NOT NULL,
        original_name VARCHAR(100),  -- NULLABLE: NULL when using full encryption
        chat_id BIGINT,
        user_id INTEGER REFERENCES Usuarios(id),
        encrypted_identity TEXT,  -- REQUIRED for full encryption mode
        role VARCHAR(20) DEFAULT 'participant' CHECK (role IN ('participant', 'officer', 'captain')),
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'banned')),
        UNIQUE(expedition_id, pirate_name),
        -- Note: original_name uniqueness only enforced when not NULL
        CONSTRAINT unique_original_name_when_not_null UNIQUE NULLS NOT DISTINCT (expedition_id, original_name)
    );

    -- Create expedition_assignments table (for consumption tracking and debt management)
    CREATE TABLE IF NOT EXISTS expedition_assignments (
        id SERIAL PRIMARY KEY,
        expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE CASCADE,
        pirate_id INTEGER REFERENCES expedition_pirates(id) ON DELETE CASCADE,
        expedition_item_id INTEGER REFERENCES expedition_items(id) ON DELETE CASCADE,
        assigned_quantity INTEGER NOT NULL,
        consumed_quantity INTEGER DEFAULT 0,
        unit_price DECIMAL(10,2) NOT NULL,
        total_cost DECIMAL(10,2) NOT NULL,
        assignment_status VARCHAR(20) DEFAULT 'assigned' CHECK (assignment_status IN ('assigned', 'partial', 'completed', 'cancelled')),
        payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'partial', 'overdue')),
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        deadline TIMESTAMP
    );

    -- Create expedition_payments table (for detailed payment tracking)
    CREATE TABLE IF NOT EXISTS expedition_payments (
        id SERIAL PRIMARY KEY,
        expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE CASCADE,
        assignment_id INTEGER REFERENCES expedition_assignments(id) ON DELETE CASCADE,
        pirate_id INTEGER REFERENCES expedition_pirates(id) ON DELETE CASCADE,
        payment_amount DECIMAL(10,2) NOT NULL,
        payment_method VARCHAR(50),
        payment_reference VARCHAR(100),
        payment_status VARCHAR(20) DEFAULT 'completed' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
        processed_by_chat_id BIGINT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    );

    -- Insert default configuration values
    INSERT INTO Configuracoes (chave, valor, descricao)
    VALUES ('frase_start', 'Bot inicializado com sucesso!', 'Mensagem exibida no comando /start')
    ON CONFLICT (chave) DO NOTHING;

    -- Initialize cash balance if not exists
    INSERT INTO CashBalance (saldo_atual)
    SELECT 0.00
    WHERE NOT EXISTS (SELECT 1 FROM CashBalance LIMIT 1);

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_usuarios_chat_id ON Usuarios(chat_id);
    CREATE INDEX IF NOT EXISTS idx_usuarios_username ON Usuarios(username);
    CREATE INDEX IF NOT EXISTS idx_vendas_comprador ON Vendas(comprador);
    CREATE INDEX IF NOT EXISTS idx_vendas_data ON Vendas(data_venda);
    CREATE INDEX IF NOT EXISTS idx_vendas_expedition ON Vendas(expedition_id);
    CREATE INDEX IF NOT EXISTS idx_itensvenda_venda_id ON ItensVenda(venda_id);
    CREATE INDEX IF NOT EXISTS idx_itensvenda_produto_id ON ItensVenda(produto_id);
    CREATE INDEX IF NOT EXISTS idx_estoque_produto_id ON Estoque(produto_id);
    CREATE INDEX IF NOT EXISTS idx_estoque_fifo ON Estoque(produto_id, data_adicao);
    CREATE INDEX IF NOT EXISTS idx_pagamentos_venda_id ON Pagamentos(venda_id);
    CREATE INDEX IF NOT EXISTS idx_smartcontracts_codigo ON SmartContracts(codigo);
    CREATE INDEX IF NOT EXISTS idx_transacoes_contract_id ON Transacoes(contract_id);
    CREATE INDEX IF NOT EXISTS idx_broadcastmessages_sender ON BroadcastMessages(sender_chat_id);
    CREATE INDEX IF NOT EXISTS idx_broadcastmessages_status ON BroadcastMessages(status);
    CREATE INDEX IF NOT EXISTS idx_broadcastmessages_created ON BroadcastMessages(created_at);
    CREATE INDEX IF NOT EXISTS idx_pollanswers_broadcast_id ON PollAnswers(broadcast_id);
    CREATE INDEX IF NOT EXISTS idx_pollanswers_poll_id ON PollAnswers(poll_id);
    CREATE INDEX IF NOT EXISTS idx_pollanswers_user_id ON PollAnswers(user_id);
    CREATE INDEX IF NOT EXISTS idx_usermasterkeys_owner_chat_id ON user_master_keys(owner_chat_id);
    CREATE INDEX IF NOT EXISTS idx_usermasterkeys_last_accessed ON user_master_keys(last_accessed);
    CREATE INDEX IF NOT EXISTS idx_cashtransactions_tipo ON CashTransactions(tipo);
    CREATE INDEX IF NOT EXISTS idx_cashtransactions_data ON CashTransactions(data_transacao);
    CREATE INDEX IF NOT EXISTS idx_cashtransactions_venda ON CashTransactions(venda_id);
    CREATE INDEX IF NOT EXISTS idx_cashtransactions_pagamento ON CashTransactions(pagamento_id);
    CREATE INDEX IF NOT EXISTS idx_expeditions_owner ON Expeditions(owner_chat_id);
    CREATE INDEX IF NOT EXISTS idx_expeditions_status ON Expeditions(status);
    CREATE INDEX IF NOT EXISTS idx_expeditions_deadline ON Expeditions(deadline);
    CREATE INDEX IF NOT EXISTS idx_expeditions_created ON Expeditions(created_at);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_expedition ON expedition_items(expedition_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_produto ON expedition_items(produto_id);
    -- REMOVED: pirate_names indexes - table removed, use expedition_pirates
    -- REMOVED: item_consumptions indexes - table migrated to expedition_assignments
    CREATE INDEX IF NOT EXISTS idx_itemmappings_product_name ON item_mappings(product_name);
    CREATE INDEX IF NOT EXISTS idx_itemmappings_custom_name ON item_mappings(custom_name);
    CREATE INDEX IF NOT EXISTS idx_itemmappings_created_by ON item_mappings(created_by_chat_id);
    CREATE INDEX IF NOT EXISTS idx_itemmappings_created_at ON item_mappings(created_at);

    -- Advanced composite indexes for optimization
    -- For export queries - status + created_at
    CREATE INDEX IF NOT EXISTS idx_expeditions_status_created ON Expeditions(status, created_at DESC);
    -- For owner dashboard - owner + status + created_at
    CREATE INDEX IF NOT EXISTS idx_expeditions_owner_status_created ON Expeditions(owner_chat_id, status, created_at DESC);
    -- For deadline monitoring - status + deadline
    CREATE INDEX IF NOT EXISTS idx_expeditions_active_deadline ON Expeditions(status, deadline) WHERE status = 'active';
    -- For expedition items with consumption tracking
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_expedition_consumed ON expedition_items(expedition_id, quantity_consumed);
    -- REMOVED: item_consumptions composite indexes - migrated to expedition_assignments
    -- For search functionality - name pattern search
    CREATE INDEX IF NOT EXISTS idx_expeditions_name_lower ON Expeditions(LOWER(name));
    -- REMOVED: pirate_names composite indexes - table removed
    -- For analytics queries - expedition items with products
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_produto_expedition ON expedition_items(produto_id, expedition_id);
    -- REMOVED: item_consumptions analytics indexes - migrated to expedition_assignments

    -- New indexes for expedition redesign tables
    -- Expedition pirates indexes
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_expedition ON expedition_pirates(expedition_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_original_name ON expedition_pirates(original_name);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_pirate_name ON expedition_pirates(pirate_name);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_chat_id ON expedition_pirates(chat_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_user_id ON expedition_pirates(user_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_status ON expedition_pirates(status);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_role ON expedition_pirates(role);
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_joined ON expedition_pirates(joined_at DESC);

    -- Expedition assignments indexes
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_expedition ON expedition_assignments(expedition_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_pirate ON expedition_assignments(pirate_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_item ON expedition_assignments(expedition_item_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_assignment_status ON expedition_assignments(assignment_status);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_payment_status ON expedition_assignments(payment_status);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_assigned ON expedition_assignments(assigned_at DESC);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_deadline ON expedition_assignments(deadline);
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_completed ON expedition_assignments(completed_at);

    -- Expedition payments indexes
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_expedition ON expedition_payments(expedition_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_assignment ON expedition_payments(assignment_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_pirate ON expedition_payments(pirate_id);
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_status ON expedition_payments(payment_status);
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_processed ON expedition_payments(processed_at DESC);
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_method ON expedition_payments(payment_method);

    -- Enhanced expedition table indexes for new fields
    CREATE INDEX IF NOT EXISTS idx_expeditions_admin_key ON expeditions(admin_key);
    CREATE INDEX IF NOT EXISTS idx_expeditions_anonymization_level ON expeditions(anonymization_level);
    CREATE INDEX IF NOT EXISTS idx_expeditions_encryption_version ON expeditions(encryption_version);
    CREATE INDEX IF NOT EXISTS idx_expeditions_target_completion ON expeditions(target_completion_date);

    -- Enhanced expedition items indexes for new fields
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_anonymized_code ON expedition_items(anonymized_item_code);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_item_status ON expedition_items(item_status);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_priority ON expedition_items(priority_level);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_updated ON expedition_items(updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_expeditionitems_target_price ON expedition_items(target_unit_price);

    -- Composite indexes for complex queries
    -- For assignment tracking by expedition and status
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_exp_status_assigned ON expedition_assignments(expedition_id, assignment_status, assigned_at DESC);
    -- For payment tracking by expedition and status
    CREATE INDEX IF NOT EXISTS idx_expeditionpayments_exp_status_processed ON expedition_payments(expedition_id, payment_status, processed_at DESC);
    -- For pirate management by expedition and status
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_exp_status_joined ON expedition_pirates(expedition_id, status, joined_at DESC);
    -- For overdue assignments monitoring
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_overdue ON expedition_assignments(assignment_status, deadline) WHERE assignment_status != 'completed' AND deadline IS NOT NULL;
    -- For financial analytics by expedition and payment status
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_exp_payment_cost ON expedition_assignments(expedition_id, payment_status, total_cost);
    -- For user activity tracking
    CREATE INDEX IF NOT EXISTS idx_expeditionpirates_user_activity ON expedition_pirates(user_id, status, joined_at DESC);
    -- For assignment deadlines and completion tracking
    CREATE INDEX IF NOT EXISTS idx_expeditionassignments_deadline_status ON expedition_assignments(deadline ASC, assignment_status) WHERE deadline IS NOT NULL;

    -- Additional performance indexes for common query patterns (Quick Win optimization)
    -- For expedition status filtering with owner (dashboard queries)
    CREATE INDEX IF NOT EXISTS idx_expeditions_status_owner_created ON Expeditions(status, owner_chat_id, created_at DESC);
    -- REMOVED: idx_consumptions_expedition_payment_consumed - table migrated to expedition_assignments
    -- For sales by expedition and buyer (debt tracking)
    CREATE INDEX IF NOT EXISTS idx_vendas_expedition_buyer ON Vendas(expedition_id, comprador) WHERE expedition_id IS NOT NULL;
    -- For unpaid sales lookup optimization
    CREATE INDEX IF NOT EXISTS idx_vendas_buyer_date ON Vendas(comprador, data_venda DESC);

    -- ===========================================================================
    -- BRAMBLER MANAGEMENT CONSOLE PERFORMANCE OPTIMIZATION INDEXES
    -- Added: 2025-10-25 to fix 10s timeout issues on /api/brambler endpoints
    -- ===========================================================================

    -- Critical: Optimize get_all_expedition_pirates JOIN query
    -- This index eliminates full table scans on expedition_pirates LEFT JOIN expeditions
    CREATE INDEX IF NOT EXISTS idx_brambler_pirates_with_expedition
        ON expedition_pirates(expedition_id, id, pirate_name, original_name)
        INCLUDE (encrypted_identity, joined_at)
        WHERE encrypted_identity IS NOT NULL OR original_name IS NOT NULL;

    -- Critical: Optimize get_all_encrypted_items JOIN query
    -- Covers the expedition_items LEFT JOIN expeditions query pattern
    CREATE INDEX IF NOT EXISTS idx_brambler_items_with_expedition
        ON expedition_items(expedition_id, id, encrypted_product_name)
        INCLUDE (encrypted_mapping, anonymized_item_code, item_type, quantity_required, quantity_consumed, item_status, created_at)
        WHERE encrypted_mapping IS NOT NULL AND encrypted_mapping != '';

    -- Optimize expeditions lookup by owner_chat_id (used in brambler filtering)
    CREATE INDEX IF NOT EXISTS idx_expeditions_owner_brambler
        ON expeditions(owner_chat_id, id, name, status);

    -- Optimize pirate queries with encryption status
    CREATE INDEX IF NOT EXISTS idx_pirates_encrypted_status
        ON expedition_pirates(expedition_id, encrypted_identity)
        WHERE encrypted_identity IS NOT NULL AND encrypted_identity != '';

    -- Optimize item queries with encryption status
    CREATE INDEX IF NOT EXISTS idx_items_encrypted_status
        ON expedition_items(expedition_id, encrypted_mapping)
        WHERE encrypted_mapping IS NOT NULL AND encrypted_mapping != '';
    """
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # First, handle migration for existing vendas table
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'vendas' AND column_name = 'expedition_id'")
                if not cursor.fetchone():
                    logger.info("Adding expedition_id column to existing vendas table")
                    cursor.execute("ALTER TABLE vendas ADD COLUMN expedition_id INTEGER REFERENCES Expeditions(id) ON DELETE SET NULL")
                    logger.info("Added expedition_id column successfully")

                # Handle migration for existing expeditions table
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'owner_key'")
                if not cursor.fetchone():
                    logger.info("Adding owner_key column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN owner_key TEXT")
                    logger.info("Added owner_key column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'owner_user_id'")
                if not cursor.fetchone():
                    logger.info("Adding owner_user_id column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN owner_user_id BIGINT")
                    logger.info("Added owner_user_id column successfully")

                # Handle migration for new dual encryption fields
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'admin_key'")
                if not cursor.fetchone():
                    logger.info("Adding admin_key column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN admin_key TEXT")
                    logger.info("Added admin_key column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'encryption_version'")
                if not cursor.fetchone():
                    logger.info("Adding encryption_version column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN encryption_version INTEGER DEFAULT 1")
                    logger.info("Added encryption_version column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'anonymization_level'")
                if not cursor.fetchone():
                    logger.info("Adding anonymization_level column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN anonymization_level VARCHAR(20) DEFAULT 'standard' CHECK (anonymization_level IN ('none', 'standard', 'enhanced', 'maximum'))")
                    logger.info("Added anonymization_level column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'description'")
                if not cursor.fetchone():
                    logger.info("Adding description column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN description TEXT")
                    logger.info("Added description column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'target_completion_date'")
                if not cursor.fetchone():
                    logger.info("Adding target_completion_date column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN target_completion_date TIMESTAMP")
                    logger.info("Added target_completion_date column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expeditions' AND column_name = 'progress_notes'")
                if not cursor.fetchone():
                    logger.info("Adding progress_notes column to existing expeditions table")
                    cursor.execute("ALTER TABLE expeditions ADD COLUMN progress_notes TEXT")
                    logger.info("Added progress_notes column successfully")

                # Handle migration for existing expedition_items table
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'encrypted_product_name'")
                if not cursor.fetchone():
                    logger.info("Adding encrypted_product_name column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN encrypted_product_name TEXT")
                    logger.info("Added encrypted_product_name column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'anonymized_item_code'")
                if not cursor.fetchone():
                    logger.info("Adding anonymized_item_code column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN anonymized_item_code VARCHAR(50)")
                    logger.info("Added anonymized_item_code column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'target_unit_price'")
                if not cursor.fetchone():
                    logger.info("Adding target_unit_price column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN target_unit_price DECIMAL(10,2)")
                    logger.info("Added target_unit_price column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'actual_avg_price'")
                if not cursor.fetchone():
                    logger.info("Adding actual_avg_price column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN actual_avg_price DECIMAL(10,2)")
                    logger.info("Added actual_avg_price column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'item_status'")
                if not cursor.fetchone():
                    logger.info("Adding item_status column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN item_status VARCHAR(20) DEFAULT 'active' CHECK (item_status IN ('active', 'completed', 'cancelled', 'suspended'))")
                    logger.info("Added item_status column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'priority_level'")
                if not cursor.fetchone():
                    logger.info("Adding priority_level column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN priority_level INTEGER DEFAULT 1 CHECK (priority_level BETWEEN 1 AND 5)")
                    logger.info("Added priority_level column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'notes'")
                if not cursor.fetchone():
                    logger.info("Adding notes column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN notes TEXT")
                    logger.info("Added notes column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'updated_at'")
                if not cursor.fetchone():
                    logger.info("Adding updated_at column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    logger.info("Added updated_at column successfully")

                # Add new columns for full item encryption support (Brambler Management Console)
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'original_product_name'")
                if not cursor.fetchone():
                    logger.info("Adding original_product_name column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN original_product_name VARCHAR(200)")
                    logger.info("Added original_product_name column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'encrypted_mapping'")
                if not cursor.fetchone():
                    logger.info("Adding encrypted_mapping column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN encrypted_mapping TEXT")
                    logger.info("Added encrypted_mapping column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'item_type'")
                if not cursor.fetchone():
                    logger.info("Adding item_type column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN item_type VARCHAR(50) DEFAULT 'product'")
                    logger.info("Added item_type column successfully")

                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'expedition_items' AND column_name = 'created_by_chat_id'")
                if not cursor.fetchone():
                    logger.info("Adding created_by_chat_id column to existing expedition_items table")
                    cursor.execute("ALTER TABLE expedition_items ADD COLUMN created_by_chat_id BIGINT")
                    logger.info("Added created_by_chat_id column successfully")

                # REMOVED: item_consumptions table migration - table has been fully migrated to expedition_assignments

                # SECURITY MIGRATION: Make original_name nullable in expedition_pirates for encryption support
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'expedition_pirates'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT is_nullable FROM information_schema.columns
                        WHERE table_name = 'expedition_pirates' AND column_name = 'original_name'
                    """)
                    result = cursor.fetchone()
                    if result and result[0] == 'NO':
                        logger.info("SECURITY: Making original_name nullable in expedition_pirates for encryption support")
                        # Drop the unique constraint first
                        cursor.execute("""
                            ALTER TABLE expedition_pirates
                            DROP CONSTRAINT IF EXISTS expedition_pirates_expedition_id_original_name_key
                        """)
                        # Make column nullable
                        cursor.execute("""
                            ALTER TABLE expedition_pirates
                            ALTER COLUMN original_name DROP NOT NULL
                        """)
                        # Add new unique constraint that allows NULLs
                        cursor.execute("""
                            ALTER TABLE expedition_pirates
                            ADD CONSTRAINT unique_original_name_when_not_null
                            UNIQUE NULLS NOT DISTINCT (expedition_id, original_name)
                        """)
                        logger.info("Successfully updated original_name column to support encryption")

                # Check if pirate_names table exists and needs migration for global mappings
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'pirate_names'")
                if cursor.fetchone():
                    # Check if we need to modify the constraint to allow NULL expedition_id for global mappings
                    cursor.execute("""
                        SELECT constraint_name FROM information_schema.table_constraints
                        WHERE table_name = 'pirate_names' AND constraint_type = 'FOREIGN KEY'
                        AND constraint_name LIKE '%expedition_id%'
                    """)
                    fk_constraint = cursor.fetchone()
                    if fk_constraint:
                        constraint_name = fk_constraint[0]
                        logger.info(f"Modifying pirate_names table to allow NULL expedition_id for global mappings")
                        # First, drop the existing foreign key constraint
                        cursor.execute(f"ALTER TABLE pirate_names DROP CONSTRAINT IF EXISTS {constraint_name}")
                        # Add the new constraint that allows NULL values
                        cursor.execute("ALTER TABLE pirate_names ADD CONSTRAINT pirate_names_expedition_id_fkey FOREIGN KEY (expedition_id) REFERENCES Expeditions(id) ON DELETE CASCADE")
                        logger.info("Successfully updated pirate_names foreign key constraint to allow NULL values")

                # Migrate existing global item mappings from pirate_names to item_mappings table
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'item_mappings'")
                if not cursor.fetchone():
                    logger.info("Creating item_mappings table and migrating data from pirate_names")
                    # The table will be created by the main SQL script below
                    # We'll migrate data after the table is created
                else:
                    # Check if migration is needed
                    cursor.execute("SELECT COUNT(*) FROM item_mappings")
                    mappings_count = cursor.fetchone()[0]
                    if mappings_count == 0:
                        logger.info("Migrating existing global item mappings from pirate_names to item_mappings")
                        cursor.execute("""
                            INSERT INTO item_mappings (product_name, custom_name, is_fantasy_generated, created_at)
                            SELECT original_name, pirate_name, TRUE, created_at
                            FROM pirate_names
                            WHERE expedition_id IS NULL
                            ON CONFLICT (product_name) DO NOTHING
                        """)
                        logger.info("Successfully migrated global item mappings to item_mappings table")

                # Now create/update all tables
                cursor.execute(create_tables_sql)

                # After tables are created, perform data migration if needed
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'item_mappings'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM item_mappings")
                    mappings_count = cursor.fetchone()[0]
                    if mappings_count == 0:
                        # Check if there are global mappings in pirate_names to migrate
                        cursor.execute("SELECT COUNT(*) FROM pirate_names WHERE expedition_id IS NULL")
                        pirate_mappings_count = cursor.fetchone()[0]
                        if pirate_mappings_count > 0:
                            logger.info(f"Migrating {pirate_mappings_count} global item mappings from pirate_names to item_mappings")
                            cursor.execute("""
                                INSERT INTO item_mappings (product_name, custom_name, is_fantasy_generated, created_at)
                                SELECT original_name, pirate_name, TRUE, created_at
                                FROM pirate_names
                                WHERE expedition_id IS NULL
                                ON CONFLICT (product_name) DO NOTHING
                            """)
                            logger.info("Successfully migrated global item mappings to item_mappings table")

                conn.commit()

        logger.info("Database schema initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def health_check_schema() -> dict:
    """
    Check if all required tables exist.

    Returns:
        Dictionary with schema health status
    """
    required_tables = [
        'usuarios', 'produtos', 'vendas', 'itensvenda',
        'estoque', 'pagamentos', 'smartcontracts',
        'transacoes', 'configuracoes', 'broadcastmessages',
        'pollanswers', 'cashbalance', 'cashtransactions',
        'expeditions', 'expedition_items',
        'expedition_pirates', 'expedition_assignments', 'expedition_payments',
        'item_mappings'
    ]

    # No legacy tables - all have been migrated or removed
    
    db_manager = get_db_manager()
    missing_tables = []
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, (table,))
                    
                    exists = cursor.fetchone()[0]
                    if not exists:
                        missing_tables.append(table)
        
        if missing_tables:
            return {
                "healthy": False,
                "message": f"Missing tables: {', '.join(missing_tables)}",
                "missing_tables": missing_tables
            }
        else:
            return {
                "healthy": True,
                "message": "All required tables present",
                "tables_count": len(required_tables)
            }
            
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Schema check failed: {str(e)}",
            "error": str(e)
        }