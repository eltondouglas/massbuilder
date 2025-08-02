import csv
import random
import string
import datetime
import uuid
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Tente importar a biblioteca de regex, se não existir, avise o usuário.
try:
    import exrex
except ImportError:
    messagebox.showerror(
        "Biblioteca Faltando",
        "A biblioteca 'exrex' é necessária para a funcionalidade de Regex.\n"
        "Por favor, instale-a executando: pip install exrex"
    )
    exit()


# --- CLASSE HELPER PARA TOOLTIPS ---
class Tooltip:
    """Cria um tooltip (dica de ajuda) para um widget tkinter."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


# --- LÓGICA DE GERAÇÃO DE DADOS (ATUALIZADA) ---

def _criar_gerador_de_campo(campo_config, total_linhas):
    """
    Cria e retorna um gerador (iterator) que produz valores para um campo
    com base em sua configuração de repetição e tipo.
    """
    tipo = campo_config.get('tipo', 'string')
    repetir_valor = campo_config.get('repeticao', 0)

    # Conjunto para garantir unicidade quando necessário
    valores_usados = set()

    def _gerar_novo_valor():
        """Gera um único valor novo, garantindo unicidade se necessário."""
        # Loop para garantir que um valor único seja gerado quando repetição for 1
        max_tentativas = total_linhas * 5
        for _ in range(max_tentativas):
            valor = _criar_valor_atomico(campo_config)
            if repetir_valor != 1 or valor not in valores_usados:
                valores_usados.add(valor)
                return valor
        raise ValueError(f"Não foi possível gerar um valor único para o campo '{campo_config['nome']}'."
                         " Verifique se o intervalo ou as opções são suficientes.")

    # --- Lógica do Gerador ---
    if repetir_valor == 0:  # Repetição aleatória
        for _ in range(total_linhas):
            yield _criar_valor_atomico(campo_config)
    else:  # Repetição controlada (1 para único, >1 para repetir N vezes)
        for _ in range(total_linhas):
            if _ % repetir_valor == 0:
                valor_atual = _gerar_novo_valor()
            yield valor_atual


def _criar_valor_atomico(campo):
    """Gera um único valor com base no tipo e limites (sem lógica de repetição)."""
    tipo = campo.get('tipo', 'string')

    if tipo == 'integer':
        min_val, max_val = campo.get('limite', (1, 100))
        return random.randint(int(min_val), int(max_val))
    elif tipo == 'float':
        min_val, max_val = campo.get('limite', (1.0, 100.0))
        num_casas = campo.get('casas_decimais', 2)
        return round(random.uniform(float(min_val), float(max_val)), num_casas)
    elif tipo == 'string':
        min_len, max_len = campo.get('limite', (5, 15))
        comprimento = random.randint(int(min_len), int(max_len))
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(comprimento))
    elif tipo == 'boolean':
        return random.choice([True, False])
    elif tipo == 'datetime':
        start_str, end_str = campo.get('limite', ('2020-01-01', '2025-12-31'))
        start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d')
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        random_date = start_date + datetime.timedelta(days=random_days)
        return random_date.strftime('%Y-%m-%d %H:%M:%S')
    elif tipo == 'uuid':
        return str(uuid.uuid4())
    elif tipo == 'lista_opcoes':
        opcoes = campo.get('opcoes', [])
        return random.choice(opcoes) if opcoes else None
    elif tipo == 'regex':
        pattern = campo.get('regex_pattern', '.*')
        try:
            return exrex.getone(pattern)
        except Exception as e:
            raise ValueError(f"Regex inválido para o campo '{campo['nome']}': {e}")
    return None


def gerar_dados_gui(configuracoes):
    """Função principal que orquestra a geração de dados e o arquivo CSV."""
    nome_arquivo = configuracoes.get('nome_arquivo', 'massa_de_dados.csv')
    if not nome_arquivo.lower().endswith('.csv'):
        nome_arquivo += '.csv'

    num_linhas = configuracoes.get('num_linhas', 100)
    campos = configuracoes.get('campos', [])

    try:
        # Validação prévia
        for campo in campos:
            if campo.get('repeticao') == 1:  # Checar se é possível gerar valores únicos
                if campo['tipo'] == 'integer':
                    min_v, max_v = campo['limite']
                    if (max_v - min_v + 1) < num_linhas:
                        raise ValueError(
                            f"Campo '{campo['nome']}': O intervalo ({max_v - min_v + 1}) é menor que o n° de linhas ({num_linhas}).")
                elif campo['tipo'] == 'lista_opcoes':
                    if len(campo['opcoes']) < num_linhas:
                        raise ValueError(
                            f"Campo '{campo['nome']}': O n° de opções ({len(campo['opcoes'])}) é menor que o n° de linhas ({num_linhas}).")

        # Cria um gerador para cada campo
        geradores = [_criar_gerador_de_campo(c, num_linhas) for c in campos]

        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([c['nome'] for c in campos])  # Cabeçalho

            for _ in range(num_linhas):
                linha = [next(g) for g in geradores]
                writer.writerow(linha)

        messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' gerado com sucesso com {num_linhas} linhas.")

    except (ValueError, TypeError) as e:
        messagebox.showerror("Erro de Geração ou Configuração", str(e))
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")


# --- INTERFACE GRÁFICA (GUI) ATUALIZADA ---

class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Massa de Dados v2.0")
        self.geometry("950x650")

        self.frames_campos = []
        self._criar_widgets()

    def _criar_widgets(self):
        # --- Frame principal e de controle ---
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(side="top", fill="x", expand=False)

        # Botões de controle com tooltips
        btn_carregar = ttk.Button(control_frame, text="Carregar Configuração", command=self.carregar_configuracao)
        btn_carregar.pack(side="left", padx=5)
        Tooltip(btn_carregar, "Carrega uma configuração salva de um arquivo .json")

        btn_salvar = ttk.Button(control_frame, text="Salvar Configuração", command=self.salvar_configuracao)
        btn_salvar.pack(side="left", padx=5)
        Tooltip(btn_salvar, "Salva a configuração atual em um arquivo .json")

        btn_limpar = ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_sessao)
        btn_limpar.pack(side="left", padx=5)
        Tooltip(btn_limpar, "Reseta a interface para começar do zero")

        # --- Frame de configurações gerais ---
        config_geral_frame = ttk.LabelFrame(self, text="Configurações Gerais", padding="10")
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)

        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nome_arquivo_var = tk.StringVar(value="massa_de_dados.csv")
        entry_nome_arquivo = ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40)
        entry_nome_arquivo.grid(row=0, column=1, padx=5, pady=5)
        Tooltip(entry_nome_arquivo, "Nome do arquivo de saída. Será salvo como .csv")

        ttk.Label(config_geral_frame, text="Quantidade de Linhas:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.num_linhas_var = tk.StringVar(value="100")
        entry_num_linhas = ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15)
        entry_num_linhas.grid(row=0, column=3, padx=5, pady=5)
        Tooltip(entry_num_linhas, "Número de registros (linhas) a serem gerados no arquivo")

        # --- Frame para os campos (colunas) ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        btn_add = ttk.Button(header_frame, text="Adicionar Campo", command=self.adicionar_campo)
        btn_add.pack(side="left")
        Tooltip(btn_add, "Adiciona uma nova coluna à sua massa de dados")

        # --- Canvas e Scrollbar ---
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.campos_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.canvas_window = self.canvas.create_window((4, 4), window=self.campos_frame, anchor="nw")
        self.campos_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        # --- Frame de Ação ---
        action_frame = ttk.Frame(self, padding="10")
        action_frame.pack(side="bottom", fill="x", expand=False)
        btn_gerar = ttk.Button(action_frame, text="Gerar Dados", command=self.iniciar_geracao, style="Accent.TButton")
        btn_gerar.pack()
        Tooltip(btn_gerar, "Inicia a geração dos dados com as configurações acima")

        try:
            self.tk.call("source", "azure.tcl")
            self.tk.call("set_theme", "light")
        except tk.TclError:
            pass  # Tema não encontrado, usa o padrão

        self.adicionar_campo()

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def adicionar_campo(self, config=None):
        config = config or {}
        frame_id = len(self.frames_campos)
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding="10")
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # --- Linha 1: Nome, Tipo, Variação, Repetição ---
        # Nome do Campo
        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w", padx=2)
        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'))
        entry_nome = ttk.Entry(campo_frame, textvariable=nome_var, width=20)
        entry_nome.grid(row=0, column=1, sticky="ew", padx=2)
        Tooltip(entry_nome, "Nome da coluna no arquivo CSV final")

        # Tipo de Dado
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w", padx=2)
        tipos = ['integer', 'float', 'string', 'boolean', 'datetime', 'uuid', 'lista_opcoes', 'regex']
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'))
        combo_tipo = ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12)
        combo_tipo.grid(row=0, column=3, sticky="ew", padx=2)
        Tooltip(combo_tipo, "Tipo de dado a ser gerado para esta coluna")

        # Repetição
        ttk.Label(campo_frame, text="Repetir:").grid(row=0, column=4, sticky="w", padx=2)
        repeticao_var = tk.StringVar(value=str(config.get('repeticao', '0')))
        spin_rep = ttk.Spinbox(campo_frame, from_=0, to=999, textvariable=repeticao_var, width=5)
        spin_rep.grid(row=0, column=5, sticky="w", padx=2)
        Tooltip(spin_rep, "Nº de vezes que um valor se repete.\n1 = Valor único\n0 = Aleatório")

        # Botão Remover
        btn_remover = ttk.Button(campo_frame, text="Remover", command=lambda: self.remover_campo(frame_id))
        btn_remover.grid(row=0, column=6, padx=15)
        Tooltip(btn_remover, "Remove esta coluna da configuração")

        # --- Linha 2: Limites e Opções ---
        label_limites = ttk.Label(campo_frame, text="Parâmetros:")
        label_limites.grid(row=1, column=0, sticky="w", padx=2, pady=5)

        # Variáveis
        limite1_var = tk.StringVar(value=str(config.get('limite', ['', ''])[0]))
        limite2_var = tk.StringVar(value=str(config.get('limite', ['', ''])[1]))
        opcoes_var = tk.StringVar(value=", ".join(config.get('opcoes', [])))
        regex_var = tk.StringVar(value=config.get('regex_pattern', ''))

        # Widgets de entrada
        entry_limite1 = ttk.Entry(campo_frame, textvariable=limite1_var)
        entry_limite2 = ttk.Entry(campo_frame, textvariable=limite2_var)
        entry_opcoes_regex = ttk.Entry(campo_frame, textvariable=opcoes_var)

        # --- Lógica para mostrar/esconder campos de parâmetros ---
        def _atualizar_parametros(*args):
            tipo = tipo_var.get()
            # Esconde todos primeiro
            entry_limite1.grid_remove()
            entry_limite2.grid_remove()
            entry_opcoes_regex.grid_remove()

            if tipo in ['integer', 'float', 'string']:
                label_limites.config(text="Min/Max:")
                Tooltip(label_limites,
                        "Valor mínimo e máximo para o tipo numérico\nComprimento mínimo e máximo para string")
                entry_limite1.grid(row=1, column=1, sticky="ew", padx=2)
                entry_limite2.grid(row=1, column=2, sticky="ew", columnspan=2, padx=2)
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:")
                Tooltip(label_limites, "Data de início e fim no formato AAAA-MM-DD")
                entry_limite1.grid(row=1, column=1, sticky="ew", padx=2)
                entry_limite2.grid(row=1, column=2, sticky="ew", columnspan=2, padx=2)
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções:")
                Tooltip(label_limites, "Lista de valores possíveis, separados por vírgula")
                entry_opcoes_regex.config(textvariable=opcoes_var)
                entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4, padx=2)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:")
                Tooltip(label_limites, "Expressão Regular para gerar os dados. Ex: [A-Z]{3}-\\d{4}")
                entry_opcoes_regex.config(textvariable=regex_var)
                entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4, padx=2)
            else:  # boolean, uuid
                label_limites.config(text="Parâmetros:")
                Tooltip(label_limites, "Este tipo de dado não requer parâmetros adicionais")

        tipo_var.trace_add("write", _atualizar_parametros)
        _atualizar_parametros()

        campo_frame.grid_columnconfigure(1, weight=1)
        campo_frame.grid_columnconfigure(3, weight=1)

        self.frames_campos.append({
            'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var,
            'repeticao': repeticao_var, 'limite1': limite1_var, 'limite2': limite2_var,
            'opcoes': opcoes_var, 'regex': regex_var
        })

    def remover_campo(self, frame_id):
        # Implementação de remover_campo... (sem alterações)
        for campo_dict in self.frames_campos:
            if campo_dict['id'] == frame_id:
                campo_dict['frame'].destroy()
                self.frames_campos.remove(campo_dict)
                break
        for i, campo_dict in enumerate(self.frames_campos):
            campo_dict['frame'].config(text=f"Campo {i + 1}")
            campo_dict['id'] = i

    def _coletar_configuracoes(self):
        try:
            config = {"nome_arquivo": self.nome_arquivo_var.get(), "num_linhas": int(self.num_linhas_var.get()),
                      "campos": []}
            if not config['campos'] and not self.frames_campos:
                messagebox.showwarning("Aviso", "Nenhum campo foi adicionado.")
                return None

            for widgets in self.frames_campos:
                tipo = widgets['tipo'].get()
                campo_cfg = {
                    "nome": widgets['nome'].get(), "tipo": tipo,
                    "repeticao": int(widgets['repeticao'].get())
                }
                if tipo in ['integer', 'float', 'string', 'datetime']:
                    campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
                elif tipo == 'lista_opcoes':
                    campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
                elif tipo == 'regex':
                    campo_cfg['regex_pattern'] = widgets['regex'].get()

                config["campos"].append(campo_cfg)
            return config
        except ValueError:
            messagebox.showerror("Erro de Entrada",
                                 "Verifique se todos os números (linhas, limites, repetição) são válidos.")
            return None

    def iniciar_geracao(self):
        config = self._coletar_configuracoes()
        if config:
            gerar_dados_gui(config)

    def salvar_configuracao(self):
        # Implementação de salvar_configuracao... (sem alterações)
        config = self._coletar_configuracoes()
        if not config: return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Sucesso", f"Configuração salva em {filepath}")

    def carregar_configuracao(self):
        # Implementação de carregar_configuracao... (sem alterações)
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.limpar_sessao(confirmar=False)
            self.nome_arquivo_var.set(config.get("nome_arquivo", "dados.csv"))
            self.num_linhas_var.set(str(config.get("num_linhas", 100)))
            for campo_config in config.get("campos", []):
                self.adicionar_campo(campo_config)

    def limpar_sessao(self, confirmar=True):
        # Implementação de limpar_sessao... (sem alterações)
        if confirmar and not messagebox.askyesno("Confirmar", "Deseja limpar todas as configurações?"): return
        self.nome_arquivo_var.set("massa_de_dados.csv")
        self.num_linhas_var.set("100")
        for campo_dict in list(self.frames_campos): campo_dict['frame'].destroy()
        self.frames_campos.clear()
        self.adicionar_campo()


if __name__ == "__main__":
    app = AppGeradorDados()
    app.mainloop()