import os
import psycopg2
from contextlib import closing
from datetime import datetime

# === CONEXÃO COM POSTGRES ===
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DB_URL)

# === USUÁRIOS ===
def verificar_login(username, password, chat_id):
    with closing(get_connection()) as conn:
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
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT nivel FROM Usuarios WHERE chat_id = %s", (chat_id,))
            row = c.fetchone()
            return row[0] if row else None

def listar_usuarios():
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute("SELECT username FROM Usuarios ORDER BY username")
            return [row[0] for row in c.fetchall()]

def adicionar_usuario(username, password, nivel="user"):
    with closing(get_connection()) as conn:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO Usuarios (username, password, nivel) VALUES (%s, %s, %s)",
                (username, password, nivel)
            )
            conn.commit()

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
