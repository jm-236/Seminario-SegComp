# cliente.py
import requests
import json
import base64
import os
from crypto_utils import assinar_dados, gerar_e_salvar_chaves

API_URL = 'http://127.0.0.1:5000'

def registrar_eleitor():
    """
    Conduz o processo de registro de um novo eleitor.
    """
    print("\n--- Registro de Novo Eleitor ---")
    cpf = input("Digite o CPF do novo eleitor: ")
    nome = input("Digite o nome completo do novo eleitor: ")

    # 1. Gerar as chaves para o eleitor
    print(f"\nGerando par de chaves para {nome}...")
    try:
        # Limpa o CPF para usar em nomes de arquivo
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        arq_pub, arq_priv = gerar_e_salvar_chaves(cpf_limpo)
        print(f"Chaves salvas em '{arq_pub}' e '{arq_priv}'.")
    except Exception as e:
        print(f"ERRO ao gerar chaves: {e}")
        return

    # 2. Ler a chave pública para enviar ao servidor
    with open(arq_pub, "r") as f:
        chave_publica_pem = f.read()

    # 3. Montar o payload para a API de registro
    payload = {
        "cpf": cpf,
        "nome": nome,
        "chave_publica_pem": chave_publica_pem
    }

    # 4. Enviar os dados para o servidor
    print("Registrando eleitor no sistema central...")
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{API_URL}/registrar_eleitor", data=json.dumps(payload), headers=headers)
        
        print("\n--- Resposta do Servidor ---")
        print(f"Status Code: {response.status_code}")
        print(f"Mensagem: {response.json()}")
        print("----------------------------")

    except requests.exceptions.ConnectionError:
        print("\nERRO: Não foi possível conectar ao servidor. Verifique se o 'servidor.py' está em execução.")
    except Exception as e:
        print(f"\nERRO inesperado ao registrar o eleitor: {e}")

def votar():
    """
    Conduz o processo de votação pelo terminal.
    """
    print("\n--- Sistema de Votação Digital ---")
    
    eleitor_cpf = input("Digite seu CPF: ")
    caminho_chave_privada = input("Digite o caminho para seu arquivo de chave privada (ex: eleitor_12345678900_privada.pem): ")
    
    if not os.path.exists(caminho_chave_privada):
        print(f"\nERRO: Arquivo de chave privada '{caminho_chave_privada}' não encontrado.")
        return

    print("\nCandidatos disponíveis:")
    print("  13 - Candidato da Esperança")
    print("  42 - Candidato da Resposta")
    print("  99 - Candidato do Futuro")
    candidato_id = input("Digite o número do seu candidato: ")
    
    voto_data = {
        "eleitor_cpf": eleitor_cpf,
        "candidato_id": candidato_id
    }
    
    print("\nGerando seu voto...")
    
    try:
        assinatura_bytes = assinar_dados(voto_data, caminho_chave_privada)
    except Exception as e:
        print(f"\nERRO ao assinar o voto: {e}")
        return

    assinatura_b64 = base64.b64encode(assinatura_bytes).decode('utf-8')
    
    payload_final = {
        "voto_data": voto_data,
        "assinatura_b64": assinatura_b64
    }
    
    print("Voto assinado com sucesso. Enviando para a urna digital...")
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{API_URL}/votar", data=json.dumps(payload_final), headers=headers)
        
        print("\n--- Resposta do Servidor ---")
        print(f"Status Code: {response.status_code}")
        print(f"Mensagem: {response.json()}")
        print("----------------------------")

    except requests.exceptions.ConnectionError:
        print("\nERRO: Não foi possível conectar ao servidor. Verifique se o 'servidor.py' está em execução.")
    except Exception as e:
        print(f"\nERRO inesperado ao enviar o voto: {e}")

def main():
    """
    Menu principal da aplicação cliente.
    """
    while True:
        print("\n===== MENU PRINCIPAL DO CLIENTE DE VOTAÇÃO =====")
        print("1. Registrar um novo eleitor")
        print("2. Votar")
        print("3. Sair")
        
        escolha = input("Escolha uma opção: ")
        
        if escolha == '1':
            registrar_eleitor()
        elif escolha == '2':
            votar()
        elif escolha == '3':
            print("Saindo...")
            break
        else:
            print("Opção inválida. Por favor, tente novamente.")

if __name__ == '__main__':
    main()