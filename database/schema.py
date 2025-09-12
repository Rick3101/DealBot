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

    -- Create Vendas table
    CREATE TABLE IF NOT EXISTS Vendas (
        id SERIAL PRIMARY KEY,
        comprador VARCHAR(100) NOT NULL,
        data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    -- Insert default configuration values
    INSERT INTO Configuracoes (chave, valor, descricao) 
    VALUES ('frase_start', 'Bot inicializado com sucesso!', 'Mensagem exibida no comando /start')
    ON CONFLICT (chave) DO NOTHING;

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_usuarios_chat_id ON Usuarios(chat_id);
    CREATE INDEX IF NOT EXISTS idx_usuarios_username ON Usuarios(username);
    CREATE INDEX IF NOT EXISTS idx_vendas_comprador ON Vendas(comprador);
    CREATE INDEX IF NOT EXISTS idx_vendas_data ON Vendas(data_venda);
    CREATE INDEX IF NOT EXISTS idx_itensvenda_venda_id ON ItensVenda(venda_id);
    CREATE INDEX IF NOT EXISTS idx_itensvenda_produto_id ON ItensVenda(produto_id);
    CREATE INDEX IF NOT EXISTS idx_estoque_produto_id ON Estoque(produto_id);
    CREATE INDEX IF NOT EXISTS idx_pagamentos_venda_id ON Pagamentos(venda_id);
    CREATE INDEX IF NOT EXISTS idx_smartcontracts_codigo ON SmartContracts(codigo);
    CREATE INDEX IF NOT EXISTS idx_transacoes_contract_id ON Transacoes(contract_id);
    """
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_tables_sql)
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
        'transacoes', 'configuracoes'
    ]
    
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