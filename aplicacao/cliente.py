# cliente.py
import requests
import json
import base64
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from crypto_utils import assinar_dados, gerar_e_salvar_chaves

API_URL = 'http://127.0.0.1:5000'

# Define a aparência geral da aplicação
ctk.set_appearance_mode("dark")  # Opções: "dark", "light", "system"
ctk.set_default_color_theme("blue")

def validar_cpf(cpf):
    """
    Valida um CPF, verificando formato, dígitos repetidos e os dígitos verificadores.
    
    Args:
        cpf: O CPF a ser validado, podendo conter ou não pontuação.

    Returns:
        True se o CPF for válido, False caso contrário.
    """
    
    cpf_limpo = ''.join(filter(str.isdigit, cpf))

    if len(cpf_limpo) != 11:
        return False

    if len(set(cpf_limpo)) == 1:
        return False

    try:
        # Cálculo do primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf_limpo[i]) * (10 - i)
        
        resto = soma % 11
        digito_verificador_1 = 0 if resto < 2 else 11 - resto

        if digito_verificador_1 != int(cpf_limpo[9]):
            return False

        # Cálculo do segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf_limpo[i]) * (11 - i)
            
        resto = soma % 11
        digito_verificador_2 = 0 if resto < 2 else 11 - resto

        if digito_verificador_2 != int(cpf_limpo[10]):
            return False

    except (ValueError, IndexError):
        
        return False

    return True

class AplicacaoCliente(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cliente de Votação Segura")
        self.geometry("400x250")

        self.grid_columnconfigure(0, weight=1)

        self.label_titulo = ctk.CTkLabel(self, text="Menu Principal", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo.grid(row=0, column=0, padx=20, pady=20)

        self.btn_registrar = ctk.CTkButton(self, text="Registrar Novo Eleitor", command=self.abrir_janela_registro)
        self.btn_registrar.grid(row=1, column=0, padx=40, pady=10, sticky="ew")

        self.btn_votar = ctk.CTkButton(self, text="Votar", command=self.abrir_janela_votacao)
        self.btn_votar.grid(row=2, column=0, padx=40, pady=10, sticky="ew")

        self.btn_apurar = ctk.CTkButton(self, text="Apurar Votos", command=self.abrir_janela_apuracao)
        self.btn_apurar.grid(row=3, column=0, padx=40, pady=10, sticky="ew")
        
        self.btn_sair = ctk.CTkButton(self, text="Sair", command=self.destroy, fg_color="red", hover_color="#C00000")
        self.btn_sair.grid(row=4, column=0, padx=40, pady=10, sticky="ew")

    def abrir_janela_registro(self):
        JanelaRegistro(self)

    def abrir_janela_votacao(self):
        JanelaVotacao(self)
        
    def abrir_janela_apuracao(self):
        JanelaApuracao(self)


class JanelaRegistro(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registrar Eleitor")
        self.geometry("400x250")
        self.transient(parent) # Mantém a janela no topo da principal
        self.grid_columnconfigure(0, weight=1)

        self.label_titulo = ctk.CTkLabel(self, text="Dados do Eleitor", font=ctk.CTkFont(size=16))
        self.label_titulo.grid(row=0, column=0, padx=20, pady=10)

        self.entry_cpf = ctk.CTkEntry(self, placeholder_text="CPF")
        self.entry_cpf.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.entry_nome = ctk.CTkEntry(self, placeholder_text="Nome Completo")
        self.entry_nome.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.btn_registrar = ctk.CTkButton(self, text="Gerar Chaves e Registrar", command=self.registrar_eleitor)
        self.btn_registrar.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

    def registrar_eleitor(self):
        cpf = self.entry_cpf.get()
        nome = self.entry_nome.get()

        if not cpf or not nome:
            messagebox.showerror("Erro de Validação", "CPF e Nome são obrigatórios.", parent=self)
            return
        
        if not validar_cpf(cpf):
            messagebox.showerror("Erro de Validação", "CPF digitado é inválido", parent=self)
            return

        try:
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            arq_pub, arq_priv = gerar_e_salvar_chaves(cpf_limpo)
            messagebox.showinfo("Chaves Geradas", f"Chaves salvas como:\n- {arq_pub}\n- {arq_priv}\nGuarde sua chave privada em local seguro!", parent=self)

            with open(arq_pub, "r") as f:
                chave_publica_pem = f.read()

            payload = {"cpf": cpf, "nome": nome, "chave_publica_pem": chave_publica_pem}
            
            response = requests.post(f"{API_URL}/registrar_eleitor", json=payload)

            if response.status_code == 201:
                messagebox.showinfo("Sucesso", response.json().get('status', 'Eleitor registrado.'), parent=self)
                self.destroy()
            else:
                messagebox.showerror("Erro no Servidor", f"Status: {response.status_code}\n{response.json().get('erro', 'Erro desconhecido')}", parent=self)
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}", parent=self)


class JanelaVotacao(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Votar")
        self.geometry("400x380")
        self.transient(parent)
        self.grid_columnconfigure(0, weight=1)

        self.caminho_chave_privada = ""

        self.entry_cpf = ctk.CTkEntry(self, placeholder_text="Digite seu CPF")
        self.entry_cpf.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.btn_selecionar_chave = ctk.CTkButton(self, text="Selecionar Chave Privada (.pem)", command=self.selecionar_chave)
        self.btn_selecionar_chave.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.label_chave = ctk.CTkLabel(self, text="Nenhuma chave selecionada", text_color="gray")
        self.label_chave.grid(row=2, column=0, padx=20, pady=(0, 10))

        # Frame para os candidatos
        self.frame_candidatos = ctk.CTkFrame(self)
        self.frame_candidatos.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.frame_candidatos.grid_columnconfigure(0, weight=1)
        
        self.label_candidatos = ctk.CTkLabel(self.frame_candidatos, text="Escolha seu Candidato:", font=ctk.CTkFont(weight="bold"))
        self.label_candidatos.grid(row=0, column=0, padx=15, pady=(10, 5))

        self.var_candidato = ctk.StringVar(value=" ")
        ctk.CTkRadioButton(self.frame_candidatos, text="10 - Lorena Borges", variable=self.var_candidato, value="10 - Lorena").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkRadioButton(self.frame_candidatos, text="4 - Caetano", variable=self.var_candidato, value="4 - Caetano").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkRadioButton(self.frame_candidatos, text="12 - Vitor Hugo", variable=self.var_candidato, value="12 - Vitor Hugo").grid(row=3, column=0, padx=20, pady=(5, 10), sticky="w")

        self.btn_votar = ctk.CTkButton(self, text="Assinar e Enviar Voto", command=self.votar)
        self.btn_votar.grid(row=4, column=0, padx=20, pady=20, sticky="ew")

    def selecionar_chave(self):
        
        PASTA_CHAVES = "chaves"
        os.makedirs(PASTA_CHAVES, exist_ok=True)
        
        self.caminho_chave_privada = filedialog.askopenfilename(
            title="Selecione sua chave privada",
            initialdir=PASTA_CHAVES,  
            filetypes=[("Arquivos PEM", "*.pem")]
        )

        if self.caminho_chave_privada:
            self.label_chave.configure(text=os.path.basename(self.caminho_chave_privada), text_color="white")
        else:
            self.label_chave.configure(text="Nenhuma chave selecionada", text_color="gray")

    def votar(self):
        eleitor_cpf = self.entry_cpf.get()
        candidato_id = self.var_candidato.get()

        if not eleitor_cpf or not self.caminho_chave_privada or candidato_id == " ":
            messagebox.showerror("Erro de Validação", "Todos os campos são obrigatórios.", parent=self)
            return
        
        if not validar_cpf(eleitor_cpf):
            messagebox.showerror("Erro de validação", "CPF digitado é inválido")
            return

        voto_data = {"eleitor_cpf": eleitor_cpf, "candidato_id": candidato_id}

        try:
            assinatura_bytes = assinar_dados(voto_data, self.caminho_chave_privada)
            assinatura_b64 = base64.b64encode(assinatura_bytes).decode('utf-8')
            payload_final = {"voto_data": voto_data, "assinatura_b64": assinatura_b64}
            
            response = requests.post(f"{API_URL}/votar", json=payload_final)

            if response.status_code == 200:
                messagebox.showinfo("Sucesso", response.json().get('status', 'Voto registrado.'), parent=self)
                self.destroy()
            # Adicionamos a verificação para o novo erro 404
            elif response.status_code == 404:
                 messagebox.showerror("Eleitor Não Encontrado", response.json().get('erro'), parent=self)
            else:
                messagebox.showerror("Erro no Servidor", f"Status: {response.status_code}\n{response.json().get('erro', 'Erro desconhecido')}", parent=self)
            
        except FileNotFoundError:
            messagebox.showerror("Erro de Arquivo", "O arquivo de chave privada não foi encontrado no caminho especificado.", parent=self)
        
        # --- BLOCO NOVO E ESPECÍFICO PARA O ERRO DE CHAVE ---
        except ValueError as e:
            # Verifica se a mensagem de erro é a esperada ao carregar uma chave errada
            if "Could not deserialize key data" in str(e):
                messagebox.showerror(
                    "Erro de Chave", 
                    "O arquivo selecionado não é uma chave privada válida.\n\n"
                    "Por favor, selecione o arquivo correto da sua chave privada (geralmente com '_privada.pem' no nome).",
                    parent=self
                )
            else:
                # Caso seja outro tipo de ValueError
                messagebox.showerror("Erro de Valor", f"Ocorreu um erro inesperado: {e}", parent=self)
        # ----------------------------------------------------

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}", parent=self)

class JanelaApuracao(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Apuração dos Votos")
        self.geometry("500x400")
        self.transient(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self, state="disabled", font=("Courier New", 12))
        self.textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.buscar_e_exibir_resultados()

    def buscar_e_exibir_resultados(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "Buscando resultados no servidor...")
        self.textbox.configure(state="disabled")
        self.update_idletasks()

        try:
            response = requests.get(f"{API_URL}/apurar")
            response.raise_for_status() # Lança um erro para status >= 400
            
            dados = response.json()
            
            texto_resultado = f"--- APURAÇÃO FINALIZADA ---\n\n"
            texto_resultado += "Resultado Final:\n"
            texto_resultado += "----------------\n"
            if dados['resultado_final']:
                for candidato, votos in dados['resultado_final'].items():
                    texto_resultado += f"Candidato {candidato}: {votos} voto(s)\n"

            else:
                texto_resultado += "Nenhum voto válido contabilizado.\n"

            texto_resultado += "\n\n"
            texto_resultado += "Auditoria de Votos Inválidos:\n"
            texto_resultado += "-----------------------------\n"
            if dados['votos_invalidos_detectados']:
                for voto_invalido in dados['votos_invalidos_detectados']:
                    texto_resultado += f"- CPF: {voto_invalido['cpf']} (Nome: {voto_invalido['nome']})\n"
                    texto_resultado += f"  Motivo: {voto_invalido['motivo']}\n"
                
            else:
                texto_resultado += "Nenhum voto inválido detectado.\n"

            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", texto_resultado)
            self.textbox.configure(state="disabled")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor.", parent=self)
            self.destroy()
        except requests.exceptions.HTTPError as e:
            messagebox.showerror("Erro no Servidor", f"O servidor retornou um erro: {e}", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}", parent=self)
            self.destroy()


if __name__ == '__main__':
    app = AplicacaoCliente()
    app.mainloop()