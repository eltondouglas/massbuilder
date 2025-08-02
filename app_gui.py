# app_gui.py
# Camada de Apresentação e Controle: versão completa com interface de abas para dados relacionais.

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import queue

from utils import Tooltip
from data_generator import run_generation_in_thread


# =============================================================================
# CLASSE PARA GERENCIAR UMA ÚNICA ABA/ARQUIVO
# =============================================================================
class FileTab(ttk.Frame):
    """Representa uma única aba na interface, contendo a configuração de um arquivo."""

    def __init__(self, parent, app_controller, nome_inicial="Arquivo 1", **kwargs):
        super().__init__(parent, **kwargs)
        self.app_controller = app_controller
        self.nome_arquivo_var = tk.StringVar(value=nome_inicial)

        self.frames_campos = []
        self.frames_sort = []

        self.num_linhas_var = tk.StringVar(value="100")
        self.separador_var = tk.StringVar(value="Vírgula (,)")
        self.codificacao_var = tk.StringVar(value="utf-8")

        self._criar_widgets()

    def _criar_widgets(self):
        config_geral_frame = ttk.LabelFrame(self, text="Configurações do Arquivo", padding="10")
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)

        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        entry_nome_arquivo = ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40)
        entry_nome_arquivo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        entry_nome_arquivo.bind("<FocusOut>", lambda e: self.app_controller.atualizar_titulo_aba(self))
        Tooltip(entry_nome_arquivo,
                "Nome final do arquivo (sem .csv). O título da aba será atualizado ao sair do campo.")

        ttk.Label(config_geral_frame, text="Linhas:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15).grid(row=0, column=3, sticky="ew",
                                                                                       padx=5, pady=2)
        ttk.Label(config_geral_frame, text="Separador:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Combobox(config_geral_frame, textvariable=self.separador_var,
                     values=list(self.app_controller.separador_map.keys())).grid(row=1, column=1, sticky="ew", padx=5,
                                                                                 pady=2)
        ttk.Label(config_geral_frame, text="Codificação:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Combobox(config_geral_frame, textvariable=self.codificacao_var,
                     values=["utf-8", "latin-1", "windows-1252", "utf-16"], state="readonly").grid(row=1, column=3,
                                                                                                   sticky="ew", padx=5,
                                                                                                   pady=2)
        config_geral_frame.grid_columnconfigure(1, weight=1);
        config_geral_frame.grid_columnconfigure(3, weight=1)

        campos_container = ttk.LabelFrame(self, text="Definição dos Campos (Colunas)", padding="10")
        campos_container.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))
        ttk.Button(campos_container, text="Adicionar Campo", command=self.adicionar_campo).pack(side="top", anchor="w",
                                                                                                pady=5)
        canvas_frame = ttk.Frame(campos_container);
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0)
        self.campos_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y");
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.campos_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.campos_frame.bind('<Configure>', lambda e: self.app_controller._update_scrollregion(self.canvas))

        sort_frame = ttk.LabelFrame(self, text="Configurações de Ordenação", padding="10")
        sort_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        ttk.Button(sort_frame, text="Adicionar Regra", command=self.adicionar_regra_sort).pack(side="top", anchor="w")
        self.sort_rules_frame = ttk.Frame(sort_frame);
        self.sort_rules_frame.pack(side="top", fill="x", expand=True, pady=5)

    def adicionar_campo(self, config=None):
        config = config or {};
        frame_id = len(self.frames_campos)
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding=10);
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # --- Variáveis do campo ---
        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'))
        tipos = ['integer', 'float', 'string', 'nome_pessoa', 'boolean', 'datetime', 'uuid', 'lista_opcoes', 'regex',
                 'chave_estrangeira']
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'))
        e_pk_var = tk.BooleanVar(value=config.get('e_pk', False))
        repeticao_var = tk.StringVar(value=str(config.get('repeticao', '0')))
        limite1_var = tk.StringVar(value=str(config.get('limite', ['', ''])[0]))
        limite2_var = tk.StringVar(value=str(config.get('limite', ['', ''])[1]))
        opcoes_var = tk.StringVar(value=", ".join(config.get('opcoes', [])))
        regex_var = tk.StringVar(value=config.get('regex_pattern', ''))
        fk_arquivo_var = tk.StringVar(value=config.get('fk_arquivo', ''))
        fk_campo_var = tk.StringVar(value=config.get('fk_campo', ''))

        # --- Widgets do campo ---
        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w");
        ttk.Entry(campo_frame, textvariable=nome_var, width=15).grid(row=0, column=1, sticky="ew")
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w");
        combo_tipo = ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12);
        combo_tipo.grid(row=0, column=3, sticky="ew")
        check_pk = ttk.Checkbutton(campo_frame, text="É Chave Primária (PK)", variable=e_pk_var,
                                   command=lambda: spin_rep.config(
                                       state="disabled") if e_pk_var.get() else spin_rep.config(state="normal"))
        check_pk.grid(row=0, column=4, sticky="w", padx=5)
        ttk.Label(campo_frame, text="Repetir:").grid(row=1, column=4, sticky="w", pady=(5, 0));
        spin_rep = ttk.Spinbox(campo_frame, from_=0, to=999, textvariable=repeticao_var, width=5);
        spin_rep.grid(row=1, column=5, sticky="w", pady=(5, 0))
        if e_pk_var.get(): spin_rep.config(state="disabled")

        action_buttons_frame = ttk.Frame(campo_frame);
        action_buttons_frame.grid(row=0, column=6, rowspan=2, padx=15)
        ttk.Button(action_buttons_frame, text="↑", width=3,
                   command=lambda fid=frame_id: self._mover_campo(fid, -1)).pack(side="left")
        ttk.Button(action_buttons_frame, text="↓", width=3,
                   command=lambda fid=frame_id: self._mover_campo(fid, 1)).pack(side="left")
        ttk.Button(action_buttons_frame, text="Remover", command=lambda index=frame_id: self.remover_campo(index)).pack(
            side="left", padx=(5, 0))

        # --- Widgets de Parâmetros (visibilidade condicional) ---
        params_frame = ttk.Frame(campo_frame);
        params_frame.grid(row=2, column=0, columnspan=7, sticky='ew', pady=(10, 0))
        params_frame.grid_columnconfigure(1, weight=1)

        label_limites = ttk.Label(params_frame, text="Parâmetros:");
        label_limites.grid(row=0, column=0, sticky="w")
        entry_limite1, entry_limite2, entry_opcoes_regex = ttk.Entry(params_frame, textvariable=limite1_var), ttk.Entry(
            params_frame, textvariable=limite2_var), ttk.Entry(params_frame, textvariable=opcoes_var)
        combo_fk_arquivo, combo_fk_campo = ttk.Combobox(params_frame, textvariable=fk_arquivo_var,
                                                        state='readonly'), ttk.Combobox(params_frame,
                                                                                        textvariable=fk_campo_var,
                                                                                        state='readonly')

        def _atualizar_parametros(*args):
            # Limpa todos os widgets de parâmetros
            for widget in params_frame.winfo_children(): widget.grid_forget()

            tipo = tipo_var.get()
            label_limites.grid(row=0, column=0, sticky="w")

            if tipo in ['integer', 'float', 'string']:
                label_limites.config(text="Min/Max:");
                entry_limite1.grid(row=0, column=1, sticky="ew");
                entry_limite2.grid(row=0, column=2, sticky="ew")
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:");
                entry_limite1.grid(row=0, column=1, sticky="ew");
                entry_limite2.grid(row=0, column=2, sticky="ew")
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções (,):");
                entry_opcoes_regex.config(textvariable=opcoes_var);
                entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=2)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:");
                entry_opcoes_regex.config(textvariable=regex_var);
                entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=2)
            elif tipo == 'chave_estrangeira':
                label_limites.config(text="Relação:")
                # Popula o combobox de arquivos
                arquivos_e_pks = self.app_controller.get_lista_de_abas_e_pks(aba_atual=self)
                combo_fk_arquivo['values'] = list(arquivos_e_pks.keys())
                combo_fk_arquivo.grid(row=0, column=1, sticky="ew")
                combo_fk_campo.grid(row=0, column=2, sticky="ew")

                def on_fk_arquivo_selecionado(event):
                    arquivo_selecionado = fk_arquivo_var.get()
                    if arquivo_selecionado in arquivos_e_pks:
                        combo_fk_campo['values'] = arquivos_e_pks[arquivo_selecionado]
                        fk_campo_var.set('')

                combo_fk_arquivo.bind("<<ComboboxSelected>>", on_fk_arquivo_selecionado)
                # Popula o campo de FK se já houver um arquivo selecionado (ao carregar config)
                if fk_arquivo_var.get(): on_fk_arquivo_selecionado(None)

        tipo_var.trace_add("write", _atualizar_parametros);
        _atualizar_parametros()

        self.frames_campos.append(
            {'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var, 'e_pk': e_pk_var,
             'repeticao': repeticao_var, 'limite1': limite1_var, 'limite2': limite2_var, 'opcoes': opcoes_var,
             'regex': regex_var, 'fk_arquivo': fk_arquivo_var, 'fk_campo': fk_campo_var})

    def _atualizar_comandos_e_titulos(self):
        self._atualizar_nomes_campos_ordenacao()
        for i, campo_dict in enumerate(self.frames_campos):
            campo_dict['id'] = i;
            campo_dict['frame'].config(text=f"Campo {i + 1}")
            for child in campo_dict['frame'].winfo_children():
                if isinstance(child, ttk.Frame):
                    action_frame = child;
                    buttons = action_frame.winfo_children()
                    if len(buttons) == 3:
                        btn_subir, btn_descer, btn_remover = buttons
                        btn_subir.config(command=lambda index=i: self._mover_campo(index, -1))
                        btn_descer.config(command=lambda index=i: self._mover_campo(index, 1))
                        btn_remover.config(command=lambda index=i: self.remover_campo(index))
                        break

    def _redesenhar_layout_campos(self):
        for campo_dict in self.frames_campos: campo_dict['frame'].pack_forget()
        for campo_dict in self.frames_campos: campo_dict['frame'].pack(fill="x", expand=True, padx=5, pady=5)
        self.app_controller.after_idle(lambda: self.app_controller._update_scrollregion(self.canvas))

    def remover_campo(self, index):
        if 0 <= index < len(self.frames_campos):
            self.frames_campos.pop(index)['frame'].destroy()
            self._atualizar_comandos_e_titulos()

    def _mover_campo(self, index, direcao):
        if (direcao == -1 and index == 0) or (direcao == 1 and index == len(self.frames_campos) - 1): return
        nova_posicao = index + direcao
        self.frames_campos[index], self.frames_campos[nova_posicao] = self.frames_campos[nova_posicao], \
        self.frames_campos[index]
        self._atualizar_comandos_e_titulos()
        self._redesenhar_layout_campos()

    def _atualizar_nomes_campos_ordenacao(self):
        nomes_campos = [f['nome'].get() for f in self.frames_campos if f['nome'].get()]
        for rule_dict in self.frames_sort:
            for widget in rule_dict['frame'].winfo_children():
                if isinstance(widget, ttk.Combobox): widget['values'] = nomes_campos; break

    def adicionar_regra_sort(self, config=None):
        config = config or {};
        rule_id = len(self.frames_sort);
        rule_frame = ttk.Frame(self.sort_rules_frame);
        rule_frame.pack(fill="x", pady=2)
        nomes_campos = [f['nome'].get() for f in self.frames_campos if f['nome'].get()]
        campo_var = tk.StringVar(value=config.get('campo', ''));
        ordem_var = tk.StringVar(value=config.get('ordem', 'Ascendente'))
        ttk.Label(rule_frame, text="Ordenar por:").pack(side="left");
        ttk.Combobox(rule_frame, textvariable=campo_var, values=nomes_campos, state="readonly", width=30).pack(
            side="left", padx=5)
        ttk.Combobox(rule_frame, textvariable=ordem_var, values=["Ascendente", "Descendente"], state="readonly",
                     width=15).pack(side="left", padx=5)
        ttk.Button(rule_frame, text="Remover", command=lambda: self.remover_regra_sort(rule_id)).pack(side="left",
                                                                                                      padx=5)
        self.frames_sort.append({'frame': rule_frame, 'id': rule_id, 'campo': campo_var, 'ordem': ordem_var})

    def remover_regra_sort(self, rule_id):
        for rule_dict in self.frames_sort:
            if rule_dict['id'] == rule_id: rule_dict['frame'].destroy(); self.frames_sort.remove(rule_dict); break
        for i, rule_dict in enumerate(self.frames_sort): rule_dict['id'] = i

    def coletar_config_aba(self):
        """Coleta a configuração completa desta aba."""
        config_aba = {
            "nome_arquivo": self.nome_arquivo_var.get(),
            "num_linhas": int(self.num_linhas_var.get()),
            "separador": self.app_controller.separador_map.get(self.separador_var.get(), self.separador_var.get()),
            "codificacao": self.codificacao_var.get(),
            "campos": [], "regras_sort": []
        }
        for widgets in self.frames_campos:
            campo_cfg = {"nome": widgets['nome'].get(), "tipo": widgets['tipo'].get(), "e_pk": widgets['e_pk'].get(),
                         "repeticao": int(widgets['repeticao'].get())}
            tipo = widgets['tipo'].get()
            if tipo in ['integer', 'float', 'string', 'datetime']:
                campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
            elif tipo == 'lista_opcoes':
                campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
            elif tipo == 'regex':
                campo_cfg['regex_pattern'] = widgets['regex'].get()
            elif tipo == 'chave_estrangeira':
                campo_cfg['fk_arquivo'] = widgets['fk_arquivo'].get()
                campo_cfg['fk_campo'] = widgets['fk_campo'].get()
            config_aba["campos"].append(campo_cfg)
        for rule_widgets in self.frames_sort: config_aba["regras_sort"].append(
            {'campo': rule_widgets['campo'].get(), 'ordem': rule_widgets['ordem'].get()})
        return config_aba

    def carregar_config(self, config):
        """Popula os widgets desta aba com uma configuração carregada."""
        self.nome_arquivo_var.set(config.get("nome_arquivo", "arquivo.csv"))
        self.num_linhas_var.set(str(config.get("num_linhas", 100)))
        self.codificacao_var.set(config.get("codificacao", "utf-8"))
        separador_salvo = config.get("separador", ",");
        self.separador_var.set(
            {v: k for k, v in self.app_controller.separador_map.items()}.get(separador_salvo, separador_salvo))
        for campo_config in config.get("campos", []): self.adicionar_campo(campo_config)
        for sort_config in config.get("regras_sort", []): self.adicionar_regra_sort(sort_config)


# =============================================================================
# CLASSE PRINCIPAL DA APLICAÇÃO
# =============================================================================
class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Dados Relacional v4.0")
        self.geometry("1024x768")

        self.result_queue = queue.Queue()
        self.separador_map = {"Vírgula (,)": ",", "Ponto e Vírgula (;)": ";", "Tab (    )": "\t", "Pipe (|)": "|"}
        self.tabs = []
        self._criar_widgets()

    def _criar_widgets(self):
        main_frame = ttk.Frame(self);
        main_frame.pack(fill="both", expand=True)
        control_frame = ttk.Frame(main_frame, padding="10");
        control_frame.pack(side="top", fill="x", expand=False)
        ttk.Button(control_frame, text="Carregar Sessão", command=self.carregar_sessao).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Salvar Sessão", command=self.salvar_sessao).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_tudo).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Adicionar Arquivo", command=self.adicionar_aba).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Remover Arquivo Atual", command=self.remover_aba_atual).pack(side="left",
                                                                                                     padx=5)

        self.notebook = ttk.Notebook(main_frame);
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        action_frame = ttk.Frame(main_frame, padding="10");
        action_frame.pack(side="bottom", fill="x", expand=False)
        self.btn_gerar = ttk.Button(action_frame, text="Gerar Todos os Arquivos", command=self.iniciar_geracao,
                                    style="Accent.TButton")
        self.btn_gerar.pack()

        self.adicionar_aba()

    def adicionar_aba(self, config=None):
        nome_aba = config['nome_arquivo'] if config else f"Arquivo {self.notebook.index('end') + 1}"
        tab = FileTab(self.notebook, self, nome_inicial=nome_aba)
        self.tabs.append(tab)
        self.notebook.add(tab, text=nome_aba)
        self.notebook.select(tab)
        if config: tab.carregar_config(config)

    def remover_aba_atual(self):
        if self.notebook.index('end') > 0:
            selected_tab_id = self.notebook.select()
            selected_widget = self.nametowidget(selected_tab_id)
            self.tabs.remove(selected_widget)
            self.notebook.forget(selected_tab_id)
        else:
            messagebox.showwarning("Aviso", "Não é possível remover o último arquivo.")

    def atualizar_titulo_aba(self, tab_widget):
        novo_nome = tab_widget.nome_arquivo_var.get()
        self.notebook.tab(tab_widget, text=novo_nome)

    def get_lista_de_abas_e_pks(self, aba_atual=None):
        """Retorna um dicionário de arquivos e suas chaves primárias."""
        resultado = {}
        for tab in self.tabs:
            if tab is not aba_atual:
                nome_arquivo = tab.nome_arquivo_var.get()
                pks = [wdg['nome'].get() for wdg in tab.frames_campos if wdg['e_pk'].get()]
                if pks: resultado[nome_arquivo] = pks
        return resultado

    def _update_scrollregion(self, canvas):
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _coletar_configuracoes(self):
        try:
            return {"arquivos": [tab.coletar_config_aba() for tab in self.tabs]}
        except Exception as e:
            messagebox.showerror("Erro ao Coletar Configurações", f"Verifique os parâmetros.\nDetalhes: {e}")
            return None

    def iniciar_geracao(self):
        config = self._coletar_configuracoes()
        if not config: return
        self.btn_gerar.config(state="disabled", text="Gerando...");
        self.update_idletasks()
        thread = threading.Thread(target=run_generation_in_thread, args=(config, self.result_queue), daemon=True)
        thread.start()
        self.after(100, self.verificar_thread)

    def verificar_thread(self):
        try:
            result = self.result_queue.get_nowait()
            self.btn_gerar.config(state="normal", text="Gerar Todos os Arquivos")
            if result['status'] == 'success':
                messagebox.showinfo("Sucesso", result['message'])
            else:
                messagebox.showerror("Erro na Geração", result['message'])
        except queue.Empty:
            self.after(100, self.verificar_thread)

    def salvar_sessao(self):
        config = self._coletar_configuracoes()
        if not config: return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Sucesso", f"Sessão salva em {filepath}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")

    def carregar_sessao(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.limpar_tudo(confirmar=False)
            for config_arquivo in config.get("arquivos", []):
                self.adicionar_aba(config_arquivo)
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Não foi possível ler o arquivo:\n{e}")

    def limpar_tudo(self, confirmar=True):
        if confirmar and not messagebox.askyesno("Confirmar",
                                                 "Deseja limpar toda a sessão (todos os arquivos)?"): return
        for tab_widget in list(self.tabs): self.notebook.forget(tab_widget)
        self.tabs.clear()
        self.adicionar_aba()