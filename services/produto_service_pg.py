import random
import os
import psycopg2
from contextlib import closing
from datetime import datetime
from database import get_db_manager

# === CONEXÃO COM POSTGRES ===
# Legacy support - keeping for backward compatibility
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Legacy function - use get_db_manager().get_connection() instead"""
    return psycopg2.connect(DB_URL)

def init_db():
    """Initialize database tables if they don't exist."""
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
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create ItensVenda table
    CREATE TABLE IF NOT EXISTS ItensVenda (
        id SERIAL PRIMARY KEY,
        venda_id INTEGER REFERENCES Vendas(id),
        produto_id INTEGER REFERENCES Produtos(id),
        quantidade INTEGER NOT NULL,
        valor_unitario DECIMAL(10,2) NOT NULL
    );

    -- Create Estoque table
    CREATE TABLE IF NOT EXISTS Estoque (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER REFERENCES Produtos(id),
        quantidade INTEGER NOT NULL,
        valor DECIMAL(10,2) NOT NULL,
        custo DECIMAL(10,2) NOT NULL,
        data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create Pagamentos table
    CREATE TABLE IF NOT EXISTS Pagamentos (
        id SERIAL PRIMARY KEY,
        venda_id INTEGER REFERENCES Vendas(id),
        valor_pago DECIMAL(10,2) NOT NULL,
        data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create SmartContracts table
    CREATE TABLE IF NOT EXISTS SmartContracts (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        codigo VARCHAR(50) NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create TransacoesSmartContract table
    CREATE TABLE IF NOT EXISTS TransacoesSmartContract (
        id SERIAL PRIMARY KEY,
        contrato_id INTEGER REFERENCES SmartContracts(id),
        descricao TEXT NOT NULL,
        confirmado BOOLEAN DEFAULT FALSE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create FraseStart table
    CREATE TABLE IF NOT EXISTS FraseStart (
        id SERIAL PRIMARY KEY,
        frase TEXT NOT NULL
    );

    -- Insert default start phrase if table is empty
    INSERT INTO FraseStart (frase) 
    SELECT 'Bot iniciado com sucesso!'
    WHERE NOT EXISTS (SELECT 1 FROM FraseStart);
    """
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(create_tables_sql)
            conn.commit()
    
    print("SUCCESS: Database tables initialized successfully")

# === USUÁRIOS ===
def verificar_login(username, password, chat_id):
    """Verify user login and update chat_id if successful."""
    db_manager = get_db_manager()
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT id FROM Usuarios WHERE username = %s AND password = %s", (username, password))
            row = c.fetchone()

            if row:
                c.execute("UPDATE Usuarios SET chat_id = %s WHERE username = %s", (chat_id, username))
                conn.commit()
                return True
            return False

def verificar_username_existe(username):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT 1 FROM Usuarios WHERE username = %s", (username,))
            return c.fetchone() is not None

def obter_nivel(chat_id):
    """Get user permission level by chat_id."""
    db_manager = get_db_manager()
    result = db_manager.execute_query(
        "SELECT nivel FROM Usuarios WHERE chat_id = %s", 
        (chat_id,), 
        fetch='one'
    )
    return result[0] if result else None

def listar_usuarios():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT username FROM Usuarios ORDER BY username")
            return [row[0] for row in c.fetchall()]

def adicionar_usuario(username, password, nivel="user"):
    """Add a new user to the database."""
    db_manager = get_db_manager()
    db_manager.execute_query(
        "INSERT INTO Usuarios (username, password, nivel) VALUES (%s, %s, %s)",
        (username, password, nivel)
    )

def remover_usuario(username):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM Usuarios WHERE username = %s", (username,))
            conn.commit()

def atualizar_username(old_username, new_username):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Usuarios SET username = %s WHERE username = %s", (new_username, old_username))
            conn.commit()

def atualizar_senha(username, new_password):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Usuarios SET password = %s WHERE username = %s", (new_password, username))
            conn.commit()

def atualizar_nivel_usuario(username, novo_nivel):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Usuarios SET nivel = %s WHERE username = %s", (novo_nivel, username))
            conn.commit()

# === PRODUTOS ===
def adicionar_produto(nome, emoji, media_file_id=None):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM Produtos WHERE LOWER(nome) = LOWER(%s)", (nome,))
            if c.fetchone()[0] > 0:
                raise ValueError(f"Já existe um produto com o nome '{nome}'.")

            c.execute(
                "INSERT INTO Produtos (nome, media_file_id, emoji, data) VALUES (%s, %s, %s, %s)",
                (nome, media_file_id, emoji, datetime.now())
            )
            conn.commit()
            return c.lastrowid

def listar_todos_produtos():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT id, nome, emoji FROM Produtos ORDER BY nome")
            return c.fetchall()

def obter_nome_produto(produto_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT nome FROM Produtos WHERE id = %s", (produto_id,))
            row = c.fetchone()
            return row[0] if row else "Produto Desconhecido"


def verificar_produto_existe(nome):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT 1 FROM Produtos WHERE LOWER(nome) = LOWER(%s)", (nome,))
            return c.fetchone() is not None

def atualizar_nome_produto(produto_id, novo_nome):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Produtos SET nome = %s WHERE id = %s", (novo_nome, produto_id))
            conn.commit()

def atualizar_emoji_produto(produto_id, novo_emoji):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Produtos SET emoji = %s WHERE id = %s", (novo_emoji, produto_id))
            conn.commit()

def atualizar_midia_produto(produto_id, media_file_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Produtos SET media_file_id = %s WHERE id = %s", (media_file_id, produto_id))
            conn.commit()

# === ESTOQUE ===
def adicionar_estoque(produto_id, quantidade, valor, custo):
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    if valor < 0 or custo < 0:
        raise ValueError("Valor e custo não podem ser negativos.")

    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute('''
                INSERT INTO Estoque (produto_id, quantidade, valor, custo, data)
                VALUES (%s, %s, %s, %s, %s)
            ''', (produto_id, quantidade, valor, custo, datetime.now()))
            conn.commit()

def obter_estoque_detalhado():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute('''
                SELECT p.nome, p.emoji, SUM(e.quantidade) as total
                FROM Estoque e
                JOIN Produtos p ON e.produto_id = p.id
                GROUP BY p.nome, p.emoji
            ''')
            return c.fetchall()

def obter_estoque_disponivel(produto_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT SUM(quantidade) FROM Estoque WHERE produto_id = %s", (produto_id,))
            result = c.fetchone()[0]
            return result if result is not None else 0

def listar_produtos_com_estoque():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute('''
                SELECT 
                    p.id, 
                    p.nome, 
                    p.emoji, 
                    COALESCE(SUM(e.quantidade), 0) as total
                FROM Produtos p
                LEFT JOIN Estoque e ON p.id = e.produto_id
                GROUP BY p.id, p.nome, p.emoji
                ORDER BY p.nome
            ''')
            return c.fetchall()


# === VENDAS ===
def registrar_venda(comprador, data_venda, pago=False):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO Vendas (comprador, data_venda, pago)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (comprador, data_venda, pago)
            )
            venda_id = c.fetchone()[0]
            conn.commit()
            return venda_id

def registrar_item_venda(venda_id, produto_id, quantidade, valor_unitario):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO ItensVenda (venda_id, produto_id, quantidade, valor_unitario)
                VALUES (%s, %s, %s, %s)
                """,
                (venda_id, produto_id, quantidade, valor_unitario)
            )
            conn.commit()

def obter_vendas():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT id, comprador, data_venda, pago FROM Vendas ORDER BY data_venda DESC")
            return c.fetchall()

def valor_total_venda(venda_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT SUM(quantidade * valor_unitario)
                FROM ItensVenda
                WHERE venda_id = %s
                """,
                (venda_id,)
            )
            result = c.fetchone()[0]
            return result if result is not None else 0

def marcar_pagamento(venda_id, pago):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE Vendas SET pago = %s WHERE id = %s", (pago, venda_id))
            conn.commit()

def obter_itens_venda(venda_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT p.nome, i.quantidade, i.valor_unitario
                FROM ItensVenda i
                JOIN Produtos p ON i.produto_id = p.id
                WHERE i.venda_id = %s
                """,
                (venda_id,)
            )
            return c.fetchall()

def deletar_venda(venda_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM ItensVenda WHERE venda_id = %s", (venda_id,))
            c.execute("DELETE FROM Vendas WHERE id = %s", (venda_id,))
            conn.commit()
# === SMART CONTRACTS ===
def criar_smartcontract(chat_id, codigo):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO SmartContracts (chat_id, codigo, criado_em)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (chat_id, codigo, datetime.now())
            )
            contract_id = c.fetchone()[0]
            conn.commit()
            return contract_id

def buscar_smartcontract_por_codigo(codigo):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT id, chat_id, codigo, criado_em FROM SmartContracts WHERE codigo = %s", (codigo,))
            return c.fetchone()

# === TRANSAÇÕES ===
def adicionar_transacao(contract_id, remetente_id, destinatario_id, descricao, valor):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO Transacoes (contract_id, remetente_id, destinatario_id, descricao, valor, data)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (contract_id, remetente_id, destinatario_id, descricao, valor, datetime.now())
            )
            transacao_id = c.fetchone()[0]
            conn.commit()
            return transacao_id

def listar_transacoes(contract_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT t.id, u1.username, u2.username, t.descricao, t.valor, t.data
                FROM Transacoes t
                JOIN Usuarios u1 ON t.remetente_id = u1.id
                JOIN Usuarios u2 ON t.destinatario_id = u2.id
                WHERE t.contract_id = %s
                ORDER BY t.data DESC
                """,
                (contract_id,)
            )
            return c.fetchall()

def deletar_transacoes_por_contrato(contract_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM Transacoes WHERE contract_id = %s", (contract_id,))
            conn.commit()

def deletar_smartcontract(contract_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            deletar_transacoes_por_contrato(contract_id)
            c.execute("DELETE FROM SmartContracts WHERE id = %s", (contract_id,))
            conn.commit()

def obter_precos_medios():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT
                    p.id,
                    p.nome,
                    ROUND(AVG(e.valor), 2) as preco_medio
                FROM Produtos p
                JOIN Estoque e ON p.id = e.produto_id
                GROUP BY p.id, p.nome
            """)
            return c.fetchall()

def get_media_file_id(produto_id):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT media_file_id FROM Produtos WHERE id = %s", (produto_id,))
            row = c.fetchone()
            return row[0] if row else None


def obter_username_por_chat_id(chat_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT username FROM Usuarios WHERE chat_id = %s", (chat_id,))
            row = c.fetchone()
            return row[0] if row else None

def validar_estoque_suficiente(itens):
    """
    Verifica se há estoque suficiente para todos os itens da venda.
    itens: lista de tuplas (produto_id, quantidade, preco)
    Retorna: (True, None, None) se tudo ok
             (False, produto_id, disponivel) se algum produto estiver em falta
    """
    with get_connection() as conn:
        with conn.cursor() as c:
            for produto_id, quantidade, _ in itens:
                c.execute(
                    "SELECT COALESCE(SUM(quantidade), 0) FROM Estoque WHERE produto_id = %s",
                    (produto_id,)
                )
                disponivel = c.fetchone()[0]

                if disponivel < quantidade:
                    return False, produto_id, disponivel

    return True, None, None

def consumir_estoque_fifo(produto_id, quantidade_necessaria):
    with get_connection() as conn:
        with conn.cursor() as c:
            # Busca entradas de estoque mais antigas primeiro
            c.execute("""
                SELECT id, quantidade
                FROM Estoque
                WHERE produto_id = %s
                ORDER BY data ASC
            """, (produto_id,))
            lotes = c.fetchall()

            for estoque_id, qtd in lotes:
                if quantidade_necessaria <= 0:
                    break

                if qtd <= quantidade_necessaria:
                    # Consome tudo e remove o lote
                    c.execute("DELETE FROM Estoque WHERE id = %s", (estoque_id,))
                    quantidade_necessaria -= qtd
                else:
                    # Atualiza o lote com o restante
                    c.execute("""
                        UPDATE Estoque
                        SET quantidade = quantidade - %s
                        WHERE id = %s
                    """, (quantidade_necessaria, estoque_id))
                    quantidade_necessaria = 0

            conn.commit()


def listar_vendas_em_aberto(filtro_nome=None):
    with get_connection() as conn:
        with conn.cursor() as c:
            query = """
                SELECT
                    v.id,
                    v.comprador,
                    SUM(i.quantidade * i.valor_unitario) as total,
                    COALESCE(p.total_pago, 0) as pago
                FROM Vendas v
                JOIN ItensVenda i ON v.id = i.venda_id
                LEFT JOIN (
                    SELECT venda_id, SUM(valor_pago) as total_pago
                    FROM Pagamentos
                    GROUP BY venda_id
                ) p ON v.id = p.venda_id
            """
            params = []

            if filtro_nome:
                query += " WHERE LOWER(v.comprador) LIKE LOWER(%s)"
                params.append(f"%{filtro_nome}%")

            query += " GROUP BY v.id, v.comprador, p.total_pago HAVING COALESCE(p.total_pago, 0) < SUM(i.quantidade * i.valor_unitario)"
            query += " ORDER BY v.id DESC"

            c.execute(query, tuple(params))
            return c.fetchall()

def obter_username_por_chat_id(chat_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT username FROM Usuarios WHERE chat_id = ?", (chat_id,))
        row = c.fetchone()
        return row[0] if row else None

def listar_vendas_nao_pagas(nome_comprador=None):
    with get_connection() as conn:
        with conn.cursor() as c:
            base_query = """
                SELECT v.id, v.comprador, p.nome, iv.quantidade, iv.valor_unitario
                FROM Vendas v
                JOIN ItensVenda iv ON v.id = iv.venda_id
                JOIN Produtos p ON iv.produto_id = p.id
                WHERE v.pago = FALSE
            """
            params = []

            if nome_comprador:
                base_query += " AND LOWER(v.comprador) = LOWER(%s)"
                params.append(nome_comprador)

            base_query += " ORDER BY v.id DESC"
            c.execute(base_query, tuple(params))
            return c.fetchall()

def obter_estoque_detalhado():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT p.nome, p.emoji, COALESCE(SUM(e.quantidade), 0)
                FROM Estoque e
                JOIN Produtos p ON e.produto_id = p.id
                GROUP BY p.nome, p.emoji
                ORDER BY p.nome
            """)
            return c.fetchall()

def atualizar_status_pago(venda_id, pago=True):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                UPDATE Vendas
                SET pago = %s
                WHERE id = %s
            """, (pago, venda_id))
            conn.commit()

def obter_frase_start():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("SELECT texto FROM FrasesStart")
            frases = c.fetchall()
            if not frases:
                return "👋 Bem-vindo!"
            return random.choice(frases)[0]

def valor_pago_venda(venda_id):
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                SELECT COALESCE(SUM(valor_pago), 0)
                FROM Pagamentos
                WHERE venda_id = %s
            """, (venda_id,))
            return c.fetchone()[0]
