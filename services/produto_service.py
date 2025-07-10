import sqlite3
import time
from datetime import datetime

DB_PATH = "sell.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# 🔸 Produto
def adicionar_produto(nome, emoji, media_file_id=None):
    attempts = 3
    for attempt in range(attempts):
        try:
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM Produtos WHERE LOWER(nome) = LOWER(?)", (nome,))
                if c.fetchone()[0] > 0:
                    raise ValueError(f"Já existe um produto com o nome '{nome}'.")

                c.execute(
                    "INSERT INTO Produtos (nome, media_file_id, emoji, data) VALUES (?, ?, ?, ?)",
                    (nome, media_file_id, emoji, datetime.now())
                )
                conn.commit()
                return c.lastrowid
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < attempts - 1:
                time.sleep(1.5)
            else:
                raise


def listar_todos_produtos():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, nome, emoji FROM Produtos ORDER BY nome")
        return c.fetchall()

# 🔸 Estoque
def adicionar_estoque(produto_id, quantidade, valor, custo):
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")
    if valor < 0 or custo < 0:
        raise ValueError("Valor e custo não podem ser negativos.")

    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO Estoque (produto_id, quantidade, valor, custo, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto_id, quantidade, valor, custo, datetime.now()))
        conn.commit()


def obter_estoque_detalhado():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT p.nome, p.emoji, SUM(e.quantidade) as total
            FROM Estoque e
            JOIN Produtos p ON e.produto_id = p.id
            GROUP BY p.nome
        ''')
        return c.fetchall()


def obter_precos_medios():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT p.nome, ROUND(AVG(e.valor), 2)
            FROM Estoque e
            JOIN Produtos p ON e.produto_id = p.id
            GROUP BY p.nome
        ''')
        return c.fetchall()


def obter_estoque_disponivel(produto_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT SUM(quantidade) FROM Estoque WHERE produto_id = ?
        ''', (produto_id,))
        return c.fetchone()[0] or 0


# 🔸 Venda (com FIFO aplicado)
def registrar_venda(nome_cliente, itens):
    """
    itens: lista de tuplas (produto_id, quantidade, valor_total)
    """
    with get_connection() as conn:
        c = conn.cursor()

        c.execute('''
            INSERT INTO Venda (nome_cliente, data)
            VALUES (?, ?)
        ''', (nome_cliente, datetime.now()))
        venda_id = c.lastrowid

        for produto_id, quantidade, total_pago in itens:
            # Registrar item na venda
            c.execute('''
                INSERT INTO ItensVenda (venda_id, produto_id, quantidade, total_pago)
                VALUES (?, ?, ?, ?)
            ''', (venda_id, produto_id, quantidade, total_pago))

            # Consumir estoque com FIFO
            aplicar_fifo(produto_id, quantidade, c)

        conn.commit()


def aplicar_fifo(produto_id, quantidade, cursor):
    cursor.execute('''
        SELECT id, quantidade FROM Estoque
        WHERE produto_id = ? AND quantidade > 0
        ORDER BY data ASC
    ''', (produto_id,))
    lotes = cursor.fetchall()

    restantes = quantidade
    for lote_id, disponivel in lotes:
        if restantes <= 0:
            break
        consumir = min(disponivel, restantes)
        cursor.execute('''
            UPDATE Estoque SET quantidade = quantidade - ? WHERE id = ?
        ''', (consumir, lote_id))
        restantes -= consumir


# 🔸 Usuários (Login e Permissões)
def verificar_login(username, password, chat_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT id FROM Usuarios WHERE username = ? AND password = ?
        ''', (username, password))
        row = c.fetchone()

        if row:
            c.execute('''
                UPDATE Usuarios SET chat_id = ? WHERE username = ?
            ''', (chat_id, username))
            conn.commit()
            return True
        return False


def verificar_username_existe(username):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 1 FROM Usuarios WHERE username = ?
        ''', (username,))
        return c.fetchone() is not None


def obter_nivel(chat_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT nivel FROM Usuarios WHERE chat_id = ?
        ''', (chat_id,))
        row = c.fetchone()
        return row[0] if row else None


# 🔸 Banco de Dados — Inicialização
def init_db():
    with get_connection() as conn:
        c = conn.cursor()

        # Produtos
        c.execute('''
            CREATE TABLE IF NOT EXISTS Produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                media_file_id TEXT,
                emoji TEXT,
                data DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        ''')

        # Estoque
        c.execute('''
            CREATE TABLE IF NOT EXISTS Estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                valor REAL NOT NULL,
                custo REAL NOT NULL,
                data DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES Produtos(id) ON DELETE CASCADE
            )
        ''')

        # Venda
        c.execute('''
            CREATE TABLE IF NOT EXISTS Venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_cliente TEXT NOT NULL,
                data DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                pago INTEGER NOT NULL DEFAULT 0 CHECK (pago IN (0, 1))
            )
        ''')

        # Itens da Venda
        c.execute('''
            CREATE TABLE IF NOT EXISTS ItensVenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                total_pago REAL NOT NULL,
                FOREIGN KEY (venda_id) REFERENCES Venda(id),
                FOREIGN KEY (produto_id) REFERENCES Produtos(id)
            )
        ''')

        # Usuários
        c.execute('''
            CREATE TABLE IF NOT EXISTS Usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                chat_id INTEGER,
                nivel TEXT NOT NULL CHECK(nivel IN ('user', 'admin', 'owner')) DEFAULT 'user'
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS Pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                valor_pago REAL NOT NULL,
                data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venda_id) REFERENCES Venda(id) ON DELETE CASCADE
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS SmartContracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                codigo TEXT NOT NULL,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Transações do contrato
        c.execute('''
            CREATE TABLE IF NOT EXISTS TransacoesContrato (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contrato_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                data DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contrato_id) REFERENCES SmartContracts(id) ON DELETE CASCADE
            )
        ''')

        # Criar usuário padrão se não existir
        c.execute('SELECT id FROM Usuarios WHERE username = ?', ('owner',))
        if not c.fetchone():
            c.execute('''
                INSERT INTO Usuarios (username, password, nivel)
                VALUES (?, ?, ?)
            ''', ('owner', 'odra31cir', 'owner'))

        conn.commit()

def listar_usuarios():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT username FROM Usuarios ORDER BY username')
        return [row[0] for row in c.fetchall()]


def adicionar_usuario(username, password, nivel="user"):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO Usuarios (username, password, nivel) VALUES (?, ?, ?)",
            (username, password, nivel)
        )
        conn.commit()


def remover_usuario(username):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM Usuarios WHERE username = ?", (username,))
        conn.commit()


def atualizar_username(old_username, new_username):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE Usuarios SET username = ? WHERE username = ?",
            (new_username, old_username)
        )
        conn.commit()


def atualizar_senha(username, new_password):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE Usuarios SET password = ? WHERE username = ?",
            (new_password, username)
        )
        conn.commit()

def verificar_produto_existe(nome):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM Produtos WHERE LOWER(nome) = LOWER(?)", (nome,))
        return c.fetchone() is not None

def atualizar_nome_produto(produto_id, novo_nome):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE Produtos SET nome = ? WHERE id = ?
        ''', (novo_nome, produto_id))
        conn.commit()


def atualizar_emoji_produto(produto_id, novo_emoji):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE Produtos SET emoji = ? WHERE id = ?
        ''', (novo_emoji, produto_id))
        conn.commit()


def atualizar_midia_produto(produto_id, media_file_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE Produtos SET media_file_id = ? WHERE id = ?
        ''', (media_file_id, produto_id))
        conn.commit()


def listar_produtos_com_estoque():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                p.id, 
                p.nome, 
                p.emoji, 
                IFNULL(SUM(e.quantidade), 0) as total
            FROM Produtos p
            LEFT JOIN Estoque e ON p.id = e.produto_id
            GROUP BY p.id
            ORDER BY p.nome
        ''')
        return c.fetchall()
    
def validar_estoque_suficiente(itens):
    with get_connection() as conn:
        c = conn.cursor()
        for produto_id, quantidade, _ in itens:
            c.execute('''
                SELECT IFNULL(SUM(quantidade), 0) FROM Estoque WHERE produto_id = ?
            ''', (produto_id,))
            total_disponivel = c.fetchone()[0]

            if quantidade > total_disponivel:
                return False, produto_id, total_disponivel
        return True, None, None
    
def obter_nome_produto(produto_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT nome FROM Produtos WHERE id = ?", (produto_id,))
        row = c.fetchone()
        return row[0] if row else "Desconhecido"

def listar_vendas_detalhadas():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                v.id AS venda_id,
                p.nome AS nome_produto,
                iv.quantidade,
                iv.total_pago
            FROM ItensVenda iv
            JOIN Venda v ON iv.venda_id = v.id
            JOIN Produtos p ON iv.produto_id = p.id
            ORDER BY v.id DESC
        ''')
        return c.fetchall()

def listar_vendas_por_comprador(nome_comprador, status=None):
    with get_connection() as conn:
        c = conn.cursor()

        # Buscar todos os itens de venda
        c.execute('''
            SELECT 
                v.id AS venda_id,
                p.nome AS nome_produto,
                iv.quantidade,
                iv.total_pago
            FROM ItensVenda iv
            JOIN Venda v ON iv.venda_id = v.id
            JOIN Produtos p ON iv.produto_id = p.id
            WHERE LOWER(v.nome_cliente) = LOWER(?)
            ORDER BY v.id DESC
        ''', (nome_comprador,))
        todas_vendas = c.fetchall()

    if status is None:
        return todas_vendas

    # Agrupar por venda_id e filtrar com base no status (pagos ou pendentes)
    vendas_filtradas = []
    vendas_agrupadas = {}

    for venda in todas_vendas:
        venda_id = venda[0]
        if venda_id not in vendas_agrupadas:
            vendas_agrupadas[venda_id] = []
        vendas_agrupadas[venda_id].append(venda)

    for grupo in vendas_agrupadas.values():
        venda_id = grupo[0][0]
        total = sum(linha[3] for linha in grupo)
        pago = valor_pago_venda(venda_id)

        if (status == "pagos" and pago >= total) or (status == "pendentes" and pago < total):
            vendas_filtradas.extend(grupo)

    return vendas_filtradas

    
def listar_vendas_nao_pagas(nome_comprador=None):
    with get_connection() as conn:
        c = conn.cursor()
        if nome_comprador:
            c.execute('''
                SELECT v.id, v.nome_cliente, p.nome, iv.quantidade, iv.total_pago
                FROM Venda v
                JOIN ItensVenda iv ON v.id = iv.venda_id
                JOIN Produtos p ON iv.produto_id = p.id
                WHERE v.pago = 0 AND LOWER(v.nome_cliente) = LOWER(?)
                ORDER BY v.id DESC
            ''', (nome_comprador,))
        else:
            c.execute('''
                SELECT v.id, v.nome_cliente, p.nome, iv.quantidade, iv.total_pago
                FROM Venda v
                JOIN ItensVenda iv ON v.id = iv.venda_id
                JOIN Produtos p ON iv.produto_id = p.id
                WHERE v.pago = 0
                ORDER BY v.id DESC
            ''')
        return c.fetchall()

def atualizar_status_pago(venda_id, pago=True):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE Venda SET pago = ? WHERE id = ?", (int(pago), venda_id))
        conn.commit()

def valor_total_venda(venda_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT SUM(total_pago) FROM ItensVenda WHERE venda_id = ?", (venda_id,))
        return c.fetchone()[0] or 0

def valor_pago_venda(venda_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT SUM(valor_pago) FROM Pagamentos WHERE venda_id = ?", (venda_id,))
        return c.fetchone()[0] or 0

def listar_vendas_em_aberto(nome_comprador=None):
    with get_connection() as conn:
        c = conn.cursor()

        filtro_nome = "AND LOWER(v.nome_cliente) = LOWER(?)" if nome_comprador else ""
        params = (nome_comprador,) if nome_comprador else ()

        c.execute(f'''
            SELECT v.id, v.nome_cliente
            FROM Venda v
            WHERE 1=1 {filtro_nome}
            ORDER BY v.id DESC
        ''', params)

        vendas = []
        for venda_id, cliente in c.fetchall():
            total = valor_total_venda(venda_id)
            pago = valor_pago_venda(venda_id)
            if pago < total:
                vendas.append((venda_id, cliente, total, pago))
        return vendas

def registrar_pagamento(venda_id, valor):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO Pagamentos (venda_id, valor_pago) VALUES (?, ?)", (venda_id, valor))
        conn.commit()

def get_media_file_id(produto_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT media_file_id FROM Produtos WHERE id = ?", (produto_id,))
        row = c.fetchone()
        return row[0] if row and row[0] else None

def criar_smart_contract(chat_id, codigo):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO SmartContracts (chat_id, codigo)
            VALUES (?, ?)
        ''', (chat_id, codigo))
        conn.commit()

def obter_smart_contract(chat_id, codigo):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT id, codigo FROM SmartContracts
            WHERE chat_id = ? AND codigo = ?
            ORDER BY id DESC LIMIT 1
        ''', (chat_id, codigo))
        return c.fetchone()


def adicionar_transacao_contrato(contrato_id, descricao):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO TransacoesContrato (contrato_id, descricao)
            VALUES (?, ?)
        ''', (contrato_id, descricao))
        conn.commit()

def listar_transacoes_contrato(contrato_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT id, descricao FROM TransacoesContrato
            WHERE contrato_id = ?
            ORDER BY id
        ''', (contrato_id,))
        return c.fetchall()  # lista de (id, descricao)

def atualizar_nivel_usuario(username, novo_nivel):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE Usuarios SET nivel = ? WHERE username = ?",
            (novo_nivel, username)
        )
        conn.commit()

def obter_username_por_chat_id(chat_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT username FROM Usuarios WHERE chat_id = ?", (chat_id,))
        row = c.fetchone()
        return row[0] if row else None
