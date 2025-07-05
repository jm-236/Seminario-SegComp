# crypto_utils.py
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

def gerar_e_salvar_chaves(cpf_eleitor):
    """
    Gera um par de chaves RSA para um eleitor e salva em arquivos .pem.
    Retorna os nomes dos arquivos da chave pública e privada.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Formata os nomes dos arquivos
    nome_arquivo_privado = f"eleitor_{cpf_eleitor}_privada.pem"
    nome_arquivo_publico = f"eleitor_{cpf_eleitor}_publica.pem"

    # Salva a chave privada em um arquivo PEM
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(nome_arquivo_privado, "wb") as f:
        f.write(pem_private)

    # Salva a chave pública em um arquivo PEM
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(nome_arquivo_publico, "wb") as f:
        f.write(pem_public)
    
    return nome_arquivo_publico, nome_arquivo_privado

def assinar_dados(dados, caminho_chave_privada):
    
    with open(caminho_chave_privada, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    dados_bytes = json.dumps(dados, sort_keys=True).encode('utf-8')
    assinatura = private_key.sign(
        dados_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return assinatura

def verificar_assinatura(assinatura_bytes, dados, chave_publica_pem_string):
    try:
        public_key = serialization.load_pem_public_key(
            chave_publica_pem_string.encode('utf-8')
        )
        dados_bytes = json.dumps(dados, sort_keys=True).encode('utf-8')
        public_key.verify(
            assinatura_bytes,
            dados_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False