# cliente.py
import requests
import json
import base64
import os
from crypto_utils import assinar_dados, gerar_e_salvar_chaves
import tkinter as tk
from tkinter import filedialog, messagebox

API_URL = 'http://127.0.0.1:5000'


class AplicacaoCliente(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cliente de Votação")
        self.geometry("300x150")

        self.btn_registrar = tk.Button(self, text="Registrar Novo Eleitor", command=self.abrir_janela_registro)
        self.btn_registrar.pack(pady=10)

        self.btn_votar = tk.Button(self, text="Votar", command=self.abrir_janela_votacao)
        self.btn_votar.pack(pady=10)

    def abrir_janela_registro(self):
        JanelaRegistro(self)

    def abrir_janela_votacao(self):
        JanelaVotacao(self)


class JanelaRegistro(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registrar Eleitor")
        self.geometry("400x300")

        tk.Label(self, text="CPF:").pack(pady=5)
        self.entry_cpf = tk.Entry(self)
        self.entry_cpf.pack(pady=5)

        tk.Label(self, text="Nome Completo:").pack(pady=5)
        self.entry_nome = tk.Entry(self)
        self.entry_nome.pack(pady=5)

        self.btn_registrar = tk.Button(self, text="Registrar", command=self.registrar_eleitor)
        self.btn_registrar.pack(pady=20)

    def registrar_eleitor(self):
        cpf = self.entry_cpf.get()
        nome = self.entry_nome.get()

        if not cpf or not nome:
            messagebox.showerror("Erro", "CPF e Nome são obrigatórios.")
            return

        try:
            # Limpa o CPF para usar em nomes de arquivo
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            arq_pub, arq_priv = gerar_e_salvar_chaves(cpf_limpo)
            messagebox.showinfo("Chaves Geradas", f"Chaves salvas em '{arq_pub}' e '{arq_priv}'.\nGuarde sua chave privada em um local seguro!")

            with open(arq_pub, "r") as f:
                chave_publica_pem = f.read()

            payload = {
                "cpf": cpf,
                "nome": nome,
                "chave_publica_pem": chave_publica_pem
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{API_URL}/registrar_eleitor", data=json.dumps(payload), headers=headers)

            if response.status_code == 201:
                messagebox.showinfo("Sucesso", response.json().get('mensagem', 'Eleitor registrado com sucesso.'))
                self.destroy()
            else:
                messagebox.showerror("Erro no Registro", f"Status: {response.status_code}\n{response.json().get('erro', 'Erro desconhecido')}")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor. Verifique se o 'servidor.py' está em execução.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado ao registrar o eleitor: {e}")


class JanelaVotacao(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Votar")
        self.geometry("400x350")
        self.caminho_chave_privada = ""

        tk.Label(self, text="CPF:").pack(pady=5)
        self.entry_cpf = tk.Entry(self)
        self.entry_cpf.pack(pady=5)

        self.btn_selecionar_chave = tk.Button(self, text="Selecionar Chave Privada", command=self.selecionar_chave)
        self.btn_selecionar_chave.pack(pady=10)
        self.label_chave = tk.Label(self, text="Nenhuma chave selecionada")
        self.label_chave.pack()

        tk.Label(self, text="Candidatos:").pack(pady=10)
        self.var_candidato = tk.StringVar(value=" ")
        tk.Radiobutton(self, text="13 - Candidato da Esperança", variable=self.var_candidato, value="13").pack(anchor=tk.W, padx=20)
        tk.Radiobutton(self, text="42 - Candidato da Resposta", variable=self.var_candidato, value="42").pack(anchor=tk.W, padx=20)
        tk.Radiobutton(self, text="99 - Candidato do Futuro", variable=self.var_candidato, value="99").pack(anchor=tk.W, padx=20)

        self.btn_votar = tk.Button(self, text="Votar", command=self.votar)
        self.btn_votar.pack(pady=20)

    def selecionar_chave(self):
        self.caminho_chave_privada = filedialog.askopenfilename(
            title="Selecione sua chave privada",
            filetypes=[("Arquivos PEM", "*.pem")]
        )
        if self.caminho_chave_privada:
            self.label_chave.config(text=os.path.basename(self.caminho_chave_privada))
        else:
            self.label_chave.config(text="Nenhuma chave selecionada")

    def votar(self):
        eleitor_cpf = self.entry_cpf.get()
        candidato_id = self.var_candidato.get()

        if not eleitor_cpf or not self.caminho_chave_privada or candidato_id == " ":
            messagebox.showerror("Erro", "Todos os campos são obrigatórios.")
            return

        if not os.path.exists(self.caminho_chave_privada):
            messagebox.showerror("Erro", f"Arquivo de chave privada não encontrado: '{self.caminho_chave_privada}'")
            return

        voto_data = {
            "eleitor_cpf": eleitor_cpf,
            "candidato_id": candidato_id
        }

        try:
            assinatura_bytes = assinar_dados(voto_data, self.caminho_chave_privada)
            assinatura_b64 = base64.b64encode(assinatura_bytes).decode('utf-8')

            payload_final = {
                "voto_data": voto_data,
                "assinatura_b64": assinatura_b64
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{API_URL}/votar", data=json.dumps(payload_final), headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Voto Registrado", response.json().get('mensagem', 'Voto registrado com sucesso.'))
                self.destroy()
            else:
                messagebox.showerror("Erro ao Votar", f"Status: {response.status_code}\n{response.json().get('erro', 'Erro desconhecido')}")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor. Verifique se o 'servidor.py' está em execução.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado ao enviar o voto: {e}")


def main():
    app = AplicacaoCliente()
    app.mainloop()


if __name__ == '__main__':
    main()