# servidor.py
import sqlite3
import json
import base64
from flask import Flask, request, jsonify
from crypto_utils import verificar_assinatura

app = Flask(__name__)
DATABASE_NAME = 'votacao_database.db'

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = get_db_connection()
    # Tabela para guardar eleitores e suas chaves públicas confiáveis
    # CPF é a chave primária, garantindo unicidade.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS eleitores (
            cpf TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            chave_publica_pem TEXT NOT NULL
        )
    ''')
    # Tabela para guardar os votos brutos recebidos (a "urna lacrada")
    # A constraint UNIQUE no eleitor_id (que será o CPF) impede votos duplicados.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleitor_cpf TEXT NOT NULL UNIQUE,
            payload_voto_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados inicializado.")


@app.route('/registrar_eleitor', methods=['POST'])
def registrar_eleitor():
    """Endpoint para registrar um novo eleitor com CPF, Nome e sua chave pública."""
    dados = request.get_json()
    if not dados or 'cpf' not in dados or 'nome' not in dados or 'chave_publica_pem' not in dados:
        return jsonify({'erro': 'Dados incompletos. É necessário enviar cpf, nome e chave_publica_pem'}), 400

    cpf = dados['cpf']
    nome = dados['nome']
    chave_publica = dados['chave_publica_pem']

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO eleitores (cpf, nome, chave_publica_pem) VALUES (?, ?, ?)',
                     (cpf, nome, chave_publica))
        conn.commit()
        conn.close()
        return jsonify({'status': f'Eleitor {nome} (CPF: {cpf}) registrado com sucesso'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'erro': f'Eleitor com CPF {cpf} já existe'}), 409


@app.route('/votar', methods=['POST'])
def votar():
    """
    Recebe um voto assinado. O payload do voto deve conter o CPF do eleitor.
    Ex: {"voto_data": {"eleitor_cpf": "123.456.789-00", "candidato_id": "..."}, "assinatura_b64": "..."}
    """
    payload_completo = request.get_json()
    if not payload_completo or 'voto_data' not in payload_completo or 'assinatura_b64' not in payload_completo:
        return jsonify({'erro': 'Payload do voto está incompleto'}), 400

    # Usamos o CPF como o identificador do eleitor no voto
    eleitor_cpf = payload_completo['voto_data'].get('eleitor_cpf')
    if not eleitor_cpf:
        return jsonify({'erro': 'CPF do eleitor não encontrado nos dados do voto'}), 400
        
    try:
        conn = get_db_connection()
        # Armazena o payload completo. A verificação será na apuração.
        conn.execute('INSERT INTO votos (eleitor_cpf, payload_voto_json) VALUES (?, ?)',
                     (eleitor_cpf, json.dumps(payload_completo)))
        conn.commit()
        conn.close()
        return jsonify({'status': f'Voto do eleitor de CPF {eleitor_cpf} recebido e armazenado'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'erro': f'O eleitor de CPF {eleitor_cpf} já votou!'}), 409


@app.route('/apurar', methods=['GET'])
def apurar_votos():
    """
    Endpoint para apurar os votos. Lê a urna, verifica cada assinatura e conta os votos.
    """
    conn = get_db_connection()
    votos_brutos = conn.execute('SELECT * FROM votos').fetchall()
    
    resultados = {}
    votos_invalidos = []

    for voto_row in votos_brutos:
        payload_completo = json.loads(voto_row['payload_voto_json'])
        
        voto_data = payload_completo['voto_data']
        assinatura_b64 = payload_completo['assinatura_b64']
        eleitor_cpf = voto_data['eleitor_cpf']
        candidato_id = voto_data['candidato_id']

        # 1. Buscar os dados do eleitor (incluindo a chave pública) no registro confiável
        eleitor_registrado = conn.execute('SELECT nome, chave_publica_pem FROM eleitores WHERE cpf = ?', (eleitor_cpf,)).fetchone()
        
        if not eleitor_registrado:
            votos_invalidos.append({'cpf': eleitor_cpf, 'nome': 'Desconhecido', 'motivo': 'Eleitor não registrado'})
            continue

        nome_eleitor = eleitor_registrado['nome']
        chave_publica_pem = eleitor_registrado['chave_publica_pem']
        assinatura_bytes = base64.b64decode(assinatura_b64)

        # 2. Verificar a assinatura
        assinatura_valida = verificar_assinatura(assinatura_bytes, voto_data, chave_publica_pem)

        # 3. Contabilizar ou descartar
        if assinatura_valida:
            resultados[candidato_id] = resultados.get(candidato_id, 0) + 1
        else:
            votos_invalidos.append({'cpf': eleitor_cpf, 'nome': nome_eleitor, 'motivo': 'Assinatura inválida'})

    conn.close()

    return jsonify({
        'status_apuracao': 'Finalizada',
        'resultado_final': resultados,
        'votos_invalidos_detectados': votos_invalidos
    }), 200


if __name__ == '__main__':
    import os
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Banco de dados antigo '{DATABASE_NAME}' removido.")
        
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)