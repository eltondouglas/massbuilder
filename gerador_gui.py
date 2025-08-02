import csv
import random
import string
import datetime
import uuid
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# --- LÓGICA DE GERAÇÃO DE DADOS (do script anterior, com pequenos ajustes) ---

def gerar_dados(configuracoes):
    """Gera uma massa de dados com base nas configurações fornecidas."""
    nome_arquivo = configuracoes.get('nome_arquivo', 'massa_de_dados.csv')
    if not nome_arquivo.lower().endswith('.csv'):
        nome_arquivo += '.csv'

    num_linhas = configuracoes.get('num_linhas', 100)
    campos = configuracoes.get('campos', [])

    try:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            cabecalho = [campo['nome'] for campo in campos]
            writer.writerow(cabecalho)

            # Estrutura para armazenar valores já usados para campos sem repetição
            dados_gerados = {campo['nome']: set() for campo in campos if not campo.get('permite_repeticao', True)}

            for i in range(num_linhas):
                linha = []
                for campo in campos:
                    valor = _gerar_valor_campo(campo, i, dados_gerados, num_linhas)
                    linha.append(valor)
                writer.writerow(linha)

        messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' gerado com sucesso com {num_linhas} linhas.")

    except ValueError as e:
        messagebox.showerror("Erro de Geração", str(e))
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")


def _gerar_valor_campo(campo, indice, dados_gerados, total_linhas):
    """Função auxiliar para gerar um único valor para um campo."""
    nome_campo = campo['nome']
    tipo = campo.get('tipo', 'string')
    variacao = campo.get('variacao', 'aleatorio')
    permite_repeticao = campo.get('permite_repeticao', True)

    # Validação para campos não repetidos
    if not permite_repeticao and tipo in ['integer', 'lista_opcoes']:
        if tipo == 'integer':
            min_val, max_val = campo.get('limite', (1, 100))
            if (max_val - min_val + 1) < total_linhas:
                raise ValueError(
                    f"Para o campo '{nome_campo}', o intervalo de inteiros ({max_val - min_val + 1}) é menor que o número de linhas ({total_linhas}), impossibilitando gerar valores únicos.")
        elif tipo == 'lista_opcoes':
            opcoes = campo.get('opcoes', [])
            if len(opcoes) < total_linhas:
                raise ValueError(
                    f"Para o campo '{nome_campo}', o número de opções ({len(opcoes)}) é menor que o número de linhas ({total_linhas}), impossibilitando gerar valores únicos.")

    tentativas_max = total_linhas * 2

    for _ in range(tentativas_max):
        valor = None
        # Lógica de geração de valor
        if variacao == 'sequencial' and tipo == 'integer':
            limite_min, _ = campo.get('limite', (1, 1))
            valor = limite_min + indice
        elif tipo == 'integer':
            min_val, max_val = campo.get('limite', (1, 100))
            valor = random.randint(min_val, max_val)
        elif tipo == 'float':
            min_val, max_val = campo.get('limite', (1.0, 100.0))
            num_casas = campo.get('casas_decimais', 2)
            valor = round(random.uniform(min_val, max_val), num_casas)
        elif tipo == 'string':
            min_len, max_len = campo.get('limite', (5, 15))
            comprimento = random.randint(min_len, max_len)
            caracteres = string.ascii_letters + string.digits
            valor = ''.join(random.choice(caracteres) for _ in range(comprimento))
        elif tipo == 'boolean':
            valor = random.choice([True, False])
        elif tipo == 'datetime':
            start_str, end_str = campo.get('limite', ('2020-01-01', '2025-12-31'))
            start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d')
            delta = end_date - start_date
            random_days = random.randint(0, delta.days)
            random_date = start_date + datetime.timedelta(days=random_days)
            valor = random_date.strftime('%Y-%m-%d %H:%M:%S')
        elif tipo == 'uuid':
            valor = str(uuid.uuid4())
        elif tipo == 'lista_opcoes':
            opcoes = campo.get('opcoes', [])
            if opcoes:
                valor = random.choice(opcoes)

        # Verifica a unicidade do valor se necessário
        if permite_repeticao or valor not in dados_gerados.get(nome_campo, set()):
            if not permite_repeticao:
                dados_gerados[nome_campo].add(valor)
            return valor

    raise ValueError(
        f"Não foi possível gerar um valor único para o campo '{nome_campo}' após {tentativas_max} tentativas. Verifique se o intervalo ou as opções são suficientes para o número de linhas.")


# --- INTERFACE GRÁFICA (GUI) ---

class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Massa de Dados")
        self.geometry("900x600")

        self.frames_campos = []
        self._criar_widgets()

    def _criar_widgets(self):
        # --- Frame principal e de controle ---
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(side="top", fill="x", expand=False)

        # Botões de controle (Salvar/Carregar/Limpar)
        ttk.Button(control_frame, text="Carregar Configuração", command=self.carregar_configuracao).pack(side="left",
                                                                                                         padx=5)
        ttk.Button(control_frame, text="Salvar Configuração", command=self.salvar_configuracao).pack(side="left",
                                                                                                     padx=5)
        ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_sessao).pack(side="left", padx=5)

        # --- Frame de configurações gerais ---
        config_geral_frame = ttk.LabelFrame(self, text="Configurações Gerais", padding="10")
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)

        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nome_arquivo_var = tk.StringVar(value="massa_de_dados.csv")
        ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40).grid(row=0, column=1, padx=5,
                                                                                         pady=5)

        ttk.Label(config_geral_frame, text="Quantidade de Linhas:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.num_linhas_var = tk.StringVar(value="100")
        ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15).grid(row=0, column=3, padx=5, pady=5)

        # --- Frame para os campos (colunas) ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        ttk.Button(header_frame, text="Adicionar Campo", command=self.adicionar_campo).pack(side="left")

        # --- Canvas e Scrollbar para a lista de campos ---
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.campos_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.canvas.create_window((4, 4), window=self.campos_frame, anchor="nw", tags="self.campos_frame")

        self.campos_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # --- Frame de Ação ---
        action_frame = ttk.Frame(self, padding="10")
        action_frame.pack(side="bottom", fill="x", expand=False)
        ttk.Button(action_frame, text="Gerar Dados", command=self.iniciar_geracao, style="Accent.TButton").pack()
        self.tk.call("source", "light.tcl")
        self.tk.call("set_theme", "light")

        # Inicia com um campo
        self.adicionar_campo()

    def adicionar_campo(self, config=None):
        if config is None:
            config = {}

        frame_id = len(self.frames_campos)
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding="10")
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # --- Widgets do campo ---
        # Nome do Campo
        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w", padx=2)
        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'))
        ttk.Entry(campo_frame, textvariable=nome_var).grid(row=0, column=1, sticky="ew", padx=2)

        # Tipo de Dado
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w", padx=2)
        tipos = ['integer', 'float', 'string', 'boolean', 'datetime', 'uuid', 'lista_opcoes']
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'))
        ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly").grid(row=0, column=3,
                                                                                              sticky="ew", padx=2)

        # Variação
        ttk.Label(campo_frame, text="Variação:").grid(row=0, column=4, sticky="w", padx=2)
        variacoes = ['aleatorio', 'sequencial']
        variacao_var = tk.StringVar(value=config.get('variacao', 'aleatorio'))
        ttk.Combobox(campo_frame, textvariable=variacao_var, values=variacoes, state="readonly").grid(row=0, column=5,
                                                                                                      sticky="ew",
                                                                                                      padx=2)

        # Repetição
        repete_var = tk.BooleanVar(value=config.get('permite_repeticao', True))
        ttk.Checkbutton(campo_frame, text="Permite Repetição", variable=repete_var).grid(row=0, column=6, padx=10)

        # Botão Remover
        ttk.Button(campo_frame, text="Remover", command=lambda: self.remover_campo(frame_id)).grid(row=0, column=7,
                                                                                                   padx=5)

        # Limites e Opções (linha 2)
        limite1_var = tk.StringVar(value=str(config.get('limite', ['', ''])[0]))
        limite2_var = tk.StringVar(value=str(config.get('limite', ['', ''])[1]))
        opcoes_var = tk.StringVar(value=", ".join(config.get('opcoes', [])))

        ttk.Label(campo_frame, text="Limites/Opções:").grid(row=1, column=0, sticky="w", padx=2, pady=5)
        entry_limite1 = ttk.Entry(campo_frame, textvariable=limite1_var)
        entry_limite2 = ttk.Entry(campo_frame, textvariable=limite2_var)
        entry_opcoes = ttk.Entry(campo_frame, textvariable=opcoes_var)

        entry_limite1.grid(row=1, column=1, sticky="ew", columnspan=2, padx=2)
        entry_limite2.grid(row=1, column=3, sticky="ew", columnspan=2, padx=2)
        entry_opcoes.grid(row=1, column=1, sticky="ew", columnspan=4, padx=2)
        entry_opcoes.grid_remove()  # Inicia escondido

        # Lógica para mostrar os campos de limite corretos
        def _atualizar_limites(*args):
            tipo_selecionado = tipo_var.get()
            entry_limite1.grid()
            entry_limite2.grid()
            entry_opcoes.grid_remove()
            if tipo_selecionado in ['integer', 'float', 'string']:
                campo_frame.nametowidget(entry_limite1.winfo_parent())[
                    'text'] = "Limite (min, max):" if tipo_selecionado != 'string' else "Comprimento (min, max):"
            elif tipo_selecionado == 'datetime':
                campo_frame.nametowidget(entry_limite1.winfo_parent())['text'] = "Data (AAAA-MM-DD):"
            elif tipo_selecionado == 'lista_opcoes':
                entry_limite1.grid_remove()
                entry_limite2.grid_remove()
                entry_opcoes.grid()
                campo_frame.nametowidget(entry_opcoes.winfo_parent())['text'] = "Opções (separadas por vírgula):"
            else:  # boolean, uuid
                entry_limite1.grid_remove()
                entry_limite2.grid_remove()

        tipo_var.trace_add("write", _atualizar_limites)
        _atualizar_limites()

        campo_frame.grid_columnconfigure(1, weight=1)
        campo_frame.grid_columnconfigure(3, weight=1)

        self.frames_campos.append({
            'frame': campo_frame,
            'id': frame_id,
            'nome': nome_var,
            'tipo': tipo_var,
            'variacao': variacao_var,
            'permite_repeticao': repete_var,
            'limite1': limite1_var,
            'limite2': limite2_var,
            'opcoes': opcoes_var
        })

    def remover_campo(self, frame_id):
        for campo_dict in self.frames_campos:
            if campo_dict['id'] == frame_id:
                campo_dict['frame'].destroy()
                self.frames_campos.remove(campo_dict)
                break
        # Renomeia os frames restantes
        for i, campo_dict in enumerate(self.frames_campos):
            campo_dict['frame'].config(text=f"Campo {i + 1}")
            campo_dict['id'] = i

    def _coletar_configuracoes(self):
        """Coleta todas as configurações da GUI e as retorna como um dicionário."""
        try:
            config = {
                "nome_arquivo": self.nome_arquivo_var.get(),
                "num_linhas": int(self.num_linhas_var.get()),
                "campos": []
            }

            for campo_widgets in self.frames_campos:
                tipo = campo_widgets['tipo'].get()
                limite1 = campo_widgets['limite1'].get()
                limite2 = campo_widgets['limite2'].get()

                campo_config = {
                    "nome": campo_widgets['nome'].get(),
                    "tipo": tipo,
                    "variacao": campo_widgets['variacao'].get(),
                    "permite_repeticao": campo_widgets['permite_repeticao'].get()
                }

                if tipo in ['integer', 'float']:
                    campo_config['limite'] = (float(limite1) if '.' in limite1 else int(limite1),
                                              float(limite2) if '.' in limite2 else int(limite2))
                    if tipo == 'float':
                        campo_config['casas_decimais'] = 2  # Pode ser adicionado na GUI depois
                elif tipo == 'string':
                    campo_config['limite'] = (int(limite1), int(limite2))
                elif tipo == 'datetime':
                    campo_config['limite'] = (limite1, limite2)
                elif tipo == 'lista_opcoes':
                    opcoes_str = campo_widgets['opcoes'].get()
                    campo_config['opcoes'] = [opt.strip() for opt in opcoes_str.split(',') if opt.strip()]

                config["campos"].append(campo_config)

            return config
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Verifique se todos os números (linhas, limites) são válidos.")
            return None
        except Exception as e:
            messagebox.showerror("Erro de Configuração", f"Ocorreu um erro ao ler as configurações: {e}")
            return None

    def iniciar_geracao(self):
        config = self._coletar_configuracoes()
        if config:
            gerar_dados(config)

    def salvar_configuracao(self):
        config = self._coletar_configuracoes()
        if not config:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Salvar Configuração"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Sucesso", f"Configuração salva em {filepath}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")

    def carregar_configuracao(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Carregar Configuração"
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.limpar_sessao(confirmar=False)  # Limpa a interface antes de carregar

                self.nome_arquivo_var.set(config.get("nome_arquivo", "dados.csv"))
                self.num_linhas_var.set(str(config.get("num_linhas", 100)))

                for campo_config in config.get("campos", []):
                    self.adicionar_campo(campo_config)

            except Exception as e:
                messagebox.showerror("Erro ao Carregar", f"Não foi possível ler o arquivo de configuração: {e}")

    def limpar_sessao(self, confirmar=True):
        if confirmar:
            if not messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar todas as configurações?"):
                return

        self.nome_arquivo_var.set("massa_de_dados.csv")
        self.num_linhas_var.set("100")

        # Remove todos os frames de campo
        for campo_dict in list(self.frames_campos):
            campo_dict['frame'].destroy()
        self.frames_campos.clear()

        # Adiciona um campo em branco para começar
        self.adicionar_campo()


if __name__ == "__main__":
    app = AppGeradorDados()
    app.mainloop()