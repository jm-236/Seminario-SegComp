# preparar_payload.py
import json

# Altere para o nome do seu arquivo de chave pública de teste
NOME_ARQUIVO_CHAVE = 'eleitor_1_privada.pem' 

# Dados do eleitor para o teste
dados_eleitor = {
    "cpf": "12345678900",
    "nome": "Fulano de Tal"
}

# Lê o conteúdo da chave pública do arquivo
try:
    with open(NOME_ARQUIVO_CHAVE, "r") as f:
        chave_pem = f.read()
except FileNotFoundError:
    print(f"Erro: Arquivo '{NOME_ARQUIVO_CHAVE}' não encontrado.")
    exit(1)

# Adiciona a chave ao payload
dados_eleitor['chave_publica_pem'] = chave_pem

# Imprime o payload final como uma string JSON válida e em uma única linha
print(json.dumps(dados_eleitor))