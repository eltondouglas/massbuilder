import csv
import random
import string
import datetime
import uuid
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Nenhuma nova biblioteca é necessária.
try:
    import exrex
except ImportError:
    messagebox.showerror("Biblioteca Faltando", "A biblioteca 'exrex' é necessária. Instale-a com: pip install exrex")
    exit()


# --- CLASSES AUXILIARES E LÓGICA DE GERAÇÃO (SEM ALTERAÇÕES) ---

class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tooltip_window = widget, text, None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text: return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25;
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True);
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left', background="#ffffe0", relief='solid',
                         borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None


def _criar_gerador_de_campo(campo_config, total_linhas):
    tipo, repetir_valor, valores_usados = campo_config.get('tipo', 'string'), campo_config.get('repeticao', 0), set()

    def _gerar_novo_valor():
        for _ in range(total_linhas * 5):
            valor = _criar_valor_atomico(campo_config)
            if repetir_valor != 1 or valor not in valores_usados: valores_usados.add(valor); return valor
        raise ValueError(f"Não foi possível gerar valor único para '{campo_config['nome']}'.")

    if repetir_valor == 0:
        for _ in range(total_linhas): yield _criar_valor_atomico(campo_config)
    else:
        for i in range(total_linhas):
            if i % repetir_valor == 0: valor_atual = _gerar_novo_valor()
            yield valor_atual


def _criar_valor_atomico(campo):
    tipo = campo.get('tipo', 'string')
    if tipo == 'integer': return random.randint(int(campo['limite'][0]), int(campo['limite'][1]))
    if tipo == 'float': return round(random.uniform(float(campo['limite'][0]), float(campo['limite'][1])), 2)
    if tipo == 'string': return ''.join(random.choice(string.ascii_letters + string.digits) for _ in
                                        range(random.randint(int(campo['limite'][0]), int(campo['limite'][1]))))
    if tipo == 'boolean': return random.choice([True, False])
    if tipo == 'datetime': start_date, end_date = datetime.datetime.strptime(campo['limite'][0],
                                                                             '%Y-%m-%d'), datetime.datetime.strptime(
        campo['limite'][1], '%Y-%m-%d'); return (
                start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))).strftime(
        '%Y-%m-%d %H:%M:%S')
    if tipo == 'uuid': return str(uuid.uuid4())
    if tipo == 'lista_opcoes': return random.choice(campo['opcoes']) if campo.get('opcoes') else None
    if tipo == 'regex':
        try:
            return exrex.getone(campo.get('regex_pattern', '.*'))
        except Exception as e:
            raise ValueError(f"Regex inválido para '{campo['nome']}': {e}")
    return None


def gerar_dados_gui(configuracoes):
    nome_arquivo, num_linhas, campos_cfg, separador, codificacao, regras_sort = \
        configuracoes.get('nome_arquivo', 'massa_de_dados.csv'), configuracoes.get('num_linhas', 100), \
            configuracoes.get('campos', []), configuracoes.get('separador', ','), \
            configuracoes.get('codificacao', 'utf-8'), configuracoes.get('regras_sort', [])

    if not nome_arquivo.lower().endswith('.csv'): nome_arquivo += '.csv'

    try:
        if num_linhas > 500000 and regras_sort:
            if not messagebox.askyesno("Aviso de Desempenho",
                                       f"Você está gerando {num_linhas} linhas com ordenação.\nIsso pode consumir bastante memória RAM.\n\nDeseja continuar?"):
                return
        for campo in campos_cfg:
            if campo.get('repeticao') == 1:
                if campo['tipo'] == 'integer':
                    min_v, max_v = int(campo['limite'][0]), int(campo['limite'][1])
                    if (max_v - min_v + 1) < num_linhas: raise ValueError(
                        f"Campo '{campo['nome']}': Intervalo ({max_v - min_v + 1}) menor que n° de linhas ({num_linhas}).")
                elif campo['tipo'] == 'lista_opcoes' and len(campo['opcoes']) < num_linhas:
                    raise ValueError(
                        f"Campo '{campo['nome']}': N° de opções ({len(campo['opcoes'])}) menor que n° de linhas ({num_linhas}).")

        cabecalho = [c['nome'] for c in campos_cfg]
        geradores = [_criar_gerador_de_campo(c, num_linhas) for c in campos_cfg]
        dados_em_memoria = [[next(g) for g in geradores] for _ in range(num_linhas)]

        if regras_sort:
            indices_sort = {nome: i for i, nome in enumerate(cabecalho)}
            for regra in reversed(regras_sort):
                nome_campo, ordem_desc = regra['campo'], regra['ordem'] == 'Descendente'
                if nome_campo in indices_sort:
                    dados_em_memoria.sort(key=lambda row: row[indices_sort[nome_campo]], reverse=ordem_desc)

        with open(nome_arquivo, 'w', newline='', encoding=codificacao) as file:
            writer = csv.writer(file, delimiter=separador)
            writer.writerow(cabecalho)
            writer.writerows(dados_em_memoria)

        messagebox.showinfo("Sucesso", f"Arquivo '{nome_arquivo}' gerado e ordenado com sucesso!")

    except (ValueError, TypeError) as e:
        messagebox.showerror("Erro de Geração ou Configuração", str(e))
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")


# --- INTERFACE GRÁFICA CORRIGIDA E ESTABILIZADA ---

class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Massa de Dados v2.6 (Estável)")
        self.geometry("950x800")

        self.separador_map = {"Vírgula (,)": ",", "Ponto e Vírgula (;)": ";", "Tab (    )": "\t", "Pipe (|)": "|"}
        self.frames_campos = []
        self.frames_sort = []
        self._criar_widgets()

    def _update_scrollregion(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _criar_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        control_frame = ttk.Frame(main_frame, padding="10");
        control_frame.pack(side="top", fill="x", expand=False)
        btn_carregar = ttk.Button(control_frame, text="Carregar Configuração", command=self.carregar_configuracao);
        btn_carregar.pack(side="left", padx=5);
        Tooltip(btn_carregar, "Carrega uma configuração salva")
        btn_salvar = ttk.Button(control_frame, text="Salvar Configuração", command=self.salvar_configuracao);
        btn_salvar.pack(side="left", padx=5);
        Tooltip(btn_salvar, "Salva a configuração atual")
        btn_limpar = ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_sessao);
        btn_limpar.pack(side="left", padx=5);
        Tooltip(btn_limpar, "Reseta a interface")

        config_geral_frame = ttk.LabelFrame(main_frame, text="Configurações Gerais", padding="10");
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, padx=5, pady=5, sticky="w");
        self.nome_arquivo_var = tk.StringVar(value="massa_de_dados.csv");
        entry_nome_arquivo = ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40);
        entry_nome_arquivo.grid(row=0, column=1, padx=5, pady=5);
        Tooltip(entry_nome_arquivo, "Nome do arquivo de saída")
        ttk.Label(config_geral_frame, text="Quantidade de Linhas:").grid(row=0, column=2, padx=5, pady=5, sticky="w");
        self.num_linhas_var = tk.StringVar(value="100");
        entry_num_linhas = ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15);
        entry_num_linhas.grid(row=0, column=3, padx=5, pady=5);
        Tooltip(entry_num_linhas, "Número de registros a serem gerados")
        ttk.Label(config_geral_frame, text="Separador:").grid(row=1, column=0, padx=5, pady=5, sticky="w");
        self.separador_var = tk.StringVar(value="Vírgula (,)");
        combo_separador = ttk.Combobox(config_geral_frame, textvariable=self.separador_var,
                                       values=list(self.separador_map.keys()));
        combo_separador.grid(row=1, column=1, padx=5, pady=5, sticky="ew");
        Tooltip(combo_separador, "Caractere separador de colunas")
        ttk.Label(config_geral_frame, text="Codificação:").grid(row=1, column=2, padx=5, pady=5, sticky="w");
        codificacoes = ["utf-8", "latin-1", "windows-1252", "utf-16"];
        self.codificacao_var = tk.StringVar(value="utf-8");
        combo_codificacao = ttk.Combobox(config_geral_frame, textvariable=self.codificacao_var, values=codificacoes,
                                         state="readonly");
        combo_codificacao.grid(row=1, column=3, padx=5, pady=5, sticky="ew");
        Tooltip(combo_codificacao, "Codificação do arquivo de texto")
        config_geral_frame.grid_columnconfigure(1, weight=1);
        config_geral_frame.grid_columnconfigure(3, weight=1)

        campos_container = ttk.LabelFrame(main_frame, text="Definição dos Campos (Colunas)", padding="10");
        campos_container.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))
        btn_add_campo = ttk.Button(campos_container, text="Adicionar Campo", command=self.adicionar_campo);
        btn_add_campo.pack(side="top", anchor="w", pady=5);
        Tooltip(btn_add_campo, "Adiciona uma nova coluna")

        canvas_frame = ttk.Frame(campos_container);
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0)
        self.campos_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.campos_frame, anchor="nw")
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        sort_frame = ttk.LabelFrame(main_frame, text="Configurações de Ordenação", padding="10");
        sort_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        btn_add_sort = ttk.Button(sort_frame, text="Adicionar Regra de Ordenação", command=self.adicionar_regra_sort);
        btn_add_sort.pack(side="top", anchor="w");
        Tooltip(btn_add_sort, "Adiciona um critério de ordenação")
        self.sort_rules_frame = ttk.Frame(sort_frame);
        self.sort_rules_frame.pack(side="top", fill="x", expand=True, pady=5)

        action_frame = ttk.Frame(main_frame, padding="10");
        action_frame.pack(side="bottom", fill="x", expand=False)
        btn_gerar = ttk.Button(action_frame, text="Gerar Dados", command=self.iniciar_geracao, style="Accent.TButton");
        btn_gerar.pack();
        Tooltip(btn_gerar, "Inicia a geração dos dados")

        try:
            self.tk.call("source", "azure.tcl"); self.tk.call("set_theme", "light")
        except tk.TclError:
            pass
        self.adicionar_campo()

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.after_idle(self._update_scrollregion)

    def adicionar_campo(self, config=None):
        config = config or {};
        frame_id = len(self.frames_campos);
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding=10);
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)
        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w", padx=2);
        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'));
        entry_nome = ttk.Entry(campo_frame, textvariable=nome_var, width=20);
        entry_nome.grid(row=0, column=1, sticky="ew", padx=2);
        Tooltip(entry_nome, "Nome da coluna no CSV")
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w", padx=2);
        tipos = ['integer', 'float', 'string', 'boolean', 'datetime', 'uuid', 'lista_opcoes', 'regex'];
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'));
        combo_tipo = ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12);
        combo_tipo.grid(row=0, column=3, sticky="ew", padx=2);
        Tooltip(combo_tipo, "Tipo de dado a ser gerado")
        ttk.Label(campo_frame, text="Repetir:").grid(row=0, column=4, sticky="w", padx=2);
        repeticao_var = tk.StringVar(value=str(config.get('repeticao', '0')));
        spin_rep = ttk.Spinbox(campo_frame, from_=0, to=999, textvariable=repeticao_var, width=5);
        spin_rep.grid(row=0, column=5, sticky="w", padx=2);
        Tooltip(spin_rep, "Nº de repetições (1=Único)")
        btn_remover = ttk.Button(campo_frame, text="Remover", command=lambda: self.remover_campo(frame_id));
        btn_remover.grid(row=0, column=6, padx=15);
        Tooltip(btn_remover, "Remove esta coluna")
        label_limites = ttk.Label(campo_frame, text="Parâmetros:");
        label_limites.grid(row=1, column=0, sticky="w", padx=2, pady=5)
        limite1_var, limite2_var, opcoes_var, regex_var = tk.StringVar(
            value=str(config.get('limite', ['', ''])[0])), tk.StringVar(
            value=str(config.get('limite', ['', ''])[1])), tk.StringVar(
            value=", ".join(config.get('opcoes', []))), tk.StringVar(value=config.get('regex_pattern', ''))
        entry_limite1, entry_limite2, entry_opcoes_regex = ttk.Entry(campo_frame, textvariable=limite1_var), ttk.Entry(
            campo_frame, textvariable=limite2_var), ttk.Entry(campo_frame, textvariable=opcoes_var)

        def _atualizar_parametros(*args):
            tipo = tipo_var.get();
            entry_limite1.grid_remove();
            entry_limite2.grid_remove();
            entry_opcoes_regex.grid_remove()
            if tipo in ['integer', 'float', 'string']:
                label_limites.config(text="Min/Max:");entry_limite1.grid(row=1, column=1, sticky="ew",
                                                                         padx=2);entry_limite2.grid(row=1, column=2,
                                                                                                    sticky="ew",
                                                                                                    columnspan=2,
                                                                                                    padx=2)
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:");entry_limite1.grid(row=1, column=1, sticky="ew",
                                                                                 padx=2);entry_limite2.grid(row=1,
                                                                                                            column=2,
                                                                                                            sticky="ew",
                                                                                                            columnspan=2,
                                                                                                            padx=2)
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções:");entry_opcoes_regex.config(
                    textvariable=opcoes_var);entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4, padx=2)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:");entry_opcoes_regex.config(
                    textvariable=regex_var);entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4, padx=2)
            else:
                label_limites.config(text="Parâmetros:")

        tipo_var.trace_add("write", _atualizar_parametros);
        _atualizar_parametros()
        self.frames_campos.append(
            {'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var, 'repeticao': repeticao_var,
             'limite1': limite1_var, 'limite2': limite2_var, 'opcoes': opcoes_var, 'regex': regex_var})
        self.after_idle(self._update_scrollregion)

    def adicionar_regra_sort(self, config=None):
        config = config or {};
        rule_id = len(self.frames_sort);
        rule_frame = ttk.Frame(self.sort_rules_frame);
        rule_frame.pack(fill="x", pady=2)
        nomes_campos = [f['nome'].get() for f in self.frames_campos if f['nome'].get()]
        ttk.Label(rule_frame, text=f"Ordenar por:").pack(side="left", padx=5);
        campo_var = tk.StringVar(value=config.get('campo', ''));
        combo_campo = ttk.Combobox(rule_frame, textvariable=campo_var, values=nomes_campos, state="readonly", width=30);
        combo_campo.pack(side="left", padx=5);
        Tooltip(combo_campo, "Escolha a coluna para ordenar")
        ordem_var = tk.StringVar(value=config.get('ordem', 'Ascendente'));
        combo_ordem = ttk.Combobox(rule_frame, textvariable=ordem_var, values=["Ascendente", "Descendente"],
                                   state="readonly", width=15);
        combo_ordem.pack(side="left", padx=5)
        btn_remover = ttk.Button(rule_frame, text="Remover", command=lambda: self.remover_regra_sort(rule_id));
        btn_remover.pack(side="left", padx=5)
        self.frames_sort.append({'frame': rule_frame, 'id': rule_id, 'campo': campo_var, 'ordem': ordem_var})

    def remover_campo(self, frame_id):
        for campo_dict in self.frames_campos:
            if campo_dict['id'] == frame_id: campo_dict['frame'].destroy();self.frames_campos.remove(campo_dict);break
        for i, campo_dict in enumerate(self.frames_campos): campo_dict['frame'].config(text=f"Campo {i + 1}");
        campo_dict['id'] = i
        self.after_idle(self._update_scrollregion)

    def remover_regra_sort(self, rule_id):
        for rule_dict in self.frames_sort:
            if rule_dict['id'] == rule_id: rule_dict['frame'].destroy();self.frames_sort.remove(rule_dict);break
        for i, rule_dict in enumerate(self.frames_sort): rule_dict['id'] = i

    # --- FUNÇÕES DE SESSÃO (SALVAR/CARREGAR/COLETAR) CORRIGIDAS E VERIFICADAS ---

    def _coletar_configuracoes(self):
        """Coleta TODAS as configurações da GUI para um dicionário."""
        try:
            config = {"nome_arquivo": self.nome_arquivo_var.get(), "num_linhas": int(self.num_linhas_var.get()),
                      "separador": self.separador_map.get(self.separador_var.get(), self.separador_var.get()),
                      "codificacao": self.codificacao_var.get(), "campos": [], "regras_sort": []}
            if not self.frames_campos:
                messagebox.showwarning("Aviso", "Nenhum campo foi adicionado.")
                return None

            for widgets in self.frames_campos:
                tipo = widgets['tipo'].get()
                campo_cfg = {"nome": widgets['nome'].get(), "tipo": tipo, "repeticao": int(widgets['repeticao'].get())}
                if tipo in ['integer', 'float', 'string', 'datetime']:
                    campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
                elif tipo == 'lista_opcoes':
                    campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
                elif tipo == 'regex':
                    campo_cfg['regex_pattern'] = widgets['regex'].get()
                config["campos"].append(campo_cfg)

            for rule_widgets in self.frames_sort:
                config["regras_sort"].append(
                    {'campo': rule_widgets['campo'].get(), 'ordem': rule_widgets['ordem'].get()})

            return config
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Verifique se os números (linhas, limites, repetição) são válidos.")
            return None

    def salvar_configuracao(self):
        """Coleta as configurações e salva em um arquivo JSON."""
        config = self._coletar_configuracoes()
        if not config: return

        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")],
                                                title="Salvar Configuração")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Sucesso", f"Configuração salva em {filepath}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")

    def carregar_configuracao(self):
        """Carrega uma configuração de um arquivo JSON e popula a GUI."""
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Carregar Configuração")
        if not filepath: return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.limpar_sessao(confirmar=False)

            self.nome_arquivo_var.set(config.get("nome_arquivo", "dados.csv"))
            self.num_linhas_var.set(str(config.get("num_linhas", 100)))
            self.codificacao_var.set(config.get("codificacao", "utf-8"))
            separador_salvo = config.get("separador", ",")
            self.separador_var.set({v: k for k, v in self.separador_map.items()}.get(separador_salvo, separador_salvo))

            for campo_config in config.get("campos", []):
                self.adicionar_campo(campo_config)
            for sort_config in config.get("regras_sort", []):
                self.adicionar_regra_sort(sort_config)
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Não foi possível ler o arquivo de configuração:\n{e}")

    def limpar_sessao(self, confirmar=True):
        if confirmar and not messagebox.askyesno("Confirmar", "Deseja limpar todas as configurações?"): return
        self.nome_arquivo_var.set("massa_de_dados.csv");
        self.num_linhas_var.set("100");
        self.separador_var.set("Vírgula (,)");
        self.codificacao_var.set("utf-8")
        for campo_dict in list(self.frames_campos): campo_dict['frame'].destroy()
        self.frames_campos.clear()
        for sort_dict in list(self.frames_sort): sort_dict['frame'].destroy()
        self.frames_sort.clear()
        self.adicionar_campo()
        self.after_idle(self._update_scrollregion)

    def iniciar_geracao(self):
        config = self._coletar_configuracoes()
        if config: gerar_dados_gui(config)


if __name__ == "__main__":
    app = AppGeradorDados()
    app.mainloop()