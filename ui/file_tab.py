# ui/file_tab.py
# Módulo que define a classe FileTab e a janela de diálogo para regras condicionais.

import tkinter as tk
from tkinter import ttk, messagebox
from utils import Tooltip


class ConditionalRuleDialog(tk.Toplevel):
    """Janela de diálogo para criar e editar uma regra de geração condicional."""

    def __init__(self, parent, todos_os_campos, campo_atual, regra_existente=None):
        super().__init__(parent)
        self.title(f"Regra Condicional para '{campo_atual}'")
        self.transient(parent)
        self.grab_set()
        self.geometry("600x400")

        self.todos_os_campos = [c for c in todos_os_campos if c != campo_atual]
        self.regra = regra_existente or {}
        self.resultado = None  # Armazena a regra criada ao salvar

        self._criar_widgets()
        self._carregar_regra()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _criar_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- SE (Condição) ---
        if_frame = ttk.LabelFrame(main_frame, text="SE (Condição)", padding="10")
        if_frame.pack(fill="x", expand=True, pady=5)

        ttk.Label(if_frame, text="O campo:").grid(row=0, column=0, sticky="w", padx=5)
        self.campo_ref_var = tk.StringVar()
        self.combo_campo_ref = ttk.Combobox(if_frame, textvariable=self.campo_ref_var, values=self.todos_os_campos,
                                            state="readonly")
        self.combo_campo_ref.grid(row=0, column=1, sticky="ew", padx=5)

        operadores = ['é igual a', 'é diferente de', 'contém', 'não contém', '>', '<', '>=', '<=']
        self.operador_var = tk.StringVar()
        ttk.Combobox(if_frame, textvariable=self.operador_var, values=operadores, state="readonly", width=15).grid(
            row=0, column=2, padx=5)

        self.valor_ref_var = tk.StringVar()
        ttk.Entry(if_frame, textvariable=self.valor_ref_var).grid(row=0, column=3, sticky="ew", padx=5)
        if_frame.grid_columnconfigure(1, weight=1)
        if_frame.grid_columnconfigure(3, weight=1)

        # --- ENTÃO (Ação se Verdadeiro) ---
        then_frame = ttk.LabelFrame(main_frame, text="ENTÃO (Ação se Verdadeiro)", padding="10")
        then_frame.pack(fill="x", expand=True, pady=5)
        self.then_action_frame = self._criar_painel_de_acao(then_frame, default_type="Valor Fixo")

        # --- SENÃO (Ação se Falso) ---
        else_frame = ttk.LabelFrame(main_frame, text="SENÃO (Ação se Falso)", padding="10")
        else_frame.pack(fill="x", expand=True, pady=5)
        self.else_action_frame = self._criar_painel_de_acao(else_frame, default_type="Usar Geração Padrão")

        # --- Botões ---
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill="x", expand=True)
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Salvar Regra", command=self.salvar, style="Accent.TButton").pack(side="right")

    def _criar_painel_de_acao(self, parent, default_type="Nulo/Vazio"):
        """Cria um painel reutilizável para definir uma ação de geração."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", expand=True)

        tipos_acao = ["Usar Geração Padrão", "Valor Fixo", "Nulo/Vazio", "integer", "float", "string", "regex",
                      "lista_opcoes"]
        tipo_var = tk.StringVar(value=default_type)
        valor1_var = tk.StringVar()
        valor2_var = tk.StringVar()

        ttk.Label(frame, text="Gerar com tipo:").grid(row=0, column=0, sticky="w")
        combo_tipo = ttk.Combobox(frame, textvariable=tipo_var, values=tipos_acao, state="readonly")
        combo_tipo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)

        label_params = ttk.Label(frame, text="Parâmetros:")
        entry1 = ttk.Entry(frame, textvariable=valor1_var)
        entry2 = ttk.Entry(frame, textvariable=valor2_var)

        def _atualizar_params_acao(*args):
            for w in [label_params, entry1, entry2]: w.grid_forget()
            tipo = tipo_var.get()
            if tipo == "Valor Fixo":
                label_params.config(text="Valor:")
                label_params.grid(row=1, column=0, sticky="w", pady=(5, 0))
                entry1.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(5, 0))
            elif tipo in ["integer", "float", "string", "datetime"]:
                label_params.config(text="Min/Max:")
                label_params.grid(row=1, column=0, sticky="w", pady=(5, 0))
                entry1.grid(row=1, column=1, sticky="ew", pady=(5, 0))
                entry2.grid(row=1, column=2, sticky="ew", pady=(5, 0))
            elif tipo in ["regex", "lista_opcoes"]:
                label_params.config(text="Padrão/Opções:")
                label_params.grid(row=1, column=0, sticky="w", pady=(5, 0))
                entry1.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(5, 0))

        tipo_var.trace_add("write", _atualizar_params_acao)
        frame.grid_columnconfigure(1, weight=1)
        _atualizar_params_acao()

        return {'frame': frame, 'tipo_var': tipo_var, 'valor1_var': valor1_var, 'valor2_var': valor2_var}

    def _coletar_acao(self, painel):
        """Coleta a configuração de um painel de ação."""
        tipo = painel['tipo_var'].get()
        acao = {'tipo': tipo}
        if tipo == 'Valor Fixo': acao['valor_fixo'] = painel['valor1_var'].get()
        if tipo in ['integer', 'float', 'string', 'datetime']: acao['limite'] = (painel['valor1_var'].get(),
                                                                                 painel['valor2_var'].get())
        if tipo == 'regex': acao['regex_pattern'] = painel['valor1_var'].get()
        if tipo == 'lista_opcoes': acao['opcoes'] = [opt.strip() for opt in painel['valor1_var'].get().split(',') if
                                                     opt.strip()]
        return acao

    def _carregar_acao(self, painel, config_acao):
        """Carrega uma configuração em um painel de ação."""
        if not config_acao:
            return

        painel['tipo_var'].set(config_acao.get('tipo', ''))

        # Verifica cada tipo de valor e define apenas se existir
        if 'valor_fixo' in config_acao:
            painel['valor1_var'].set(config_acao['valor_fixo'])

        if 'limite' in config_acao:
            limite = config_acao['limite']
            if isinstance(limite, (list, tuple)) and len(limite) >= 2:
                painel['valor1_var'].set(limite[0])
                painel['valor2_var'].set(limite[1])

        if 'regex_pattern' in config_acao:
            painel['valor1_var'].set(config_acao['regex_pattern'])

        if 'opcoes' in config_acao:
            painel['valor1_var'].set(", ".join(config_acao['opcoes']))

    def _carregar_regra(self):
        """Carrega uma regra existente na UI do diálogo."""
        self.campo_ref_var.set(self.regra.get('campo_ref', ''))
        self.operador_var.set(self.regra.get('operador', 'é igual a'))
        self.valor_ref_var.set(self.regra.get('valor_ref', ''))
        self._carregar_acao(self.then_action_frame, self.regra.get('acao_verdadeiro'))
        self._carregar_acao(self.else_action_frame, self.regra.get('acao_falso'))

    def _on_cancel(self):
        self.resultado = None  # Garante que nada é retornado
        self.destroy()

    def salvar(self):
        """Coleta os dados da UI e os armazena para serem recuperados pela janela principal."""
        if not self.campo_ref_var.get() or not self.operador_var.get():
            messagebox.showwarning("Incompleto", "A condição (campo, operador) deve ser preenchida.", parent=self)
            return

        self.resultado = {
            'campo_ref': self.campo_ref_var.get(),
            'operador': self.operador_var.get(),
            'valor_ref': self.valor_ref_var.get(),
            'acao_verdadeiro': self._coletar_acao(self.then_action_frame),
            'acao_falso': self._coletar_acao(self.else_action_frame)
        }
        self.destroy()


class FileTab(ttk.Frame):
    """Representa uma única aba na interface, contendo a configuração de um arquivo."""

    def __init__(self, parent, app_controller, nome_inicial="Arquivo 1", **kwargs):
        super().__init__(parent, **kwargs)
        self.app_controller = app_controller
        self.nome_arquivo_var = tk.StringVar(value=nome_inicial)
        self.frames_campos, self.frames_sort = [], []
        self.num_linhas_var = tk.StringVar(value="100")
        self.separador_var = tk.StringVar(value="Vírgula (,)")
        self.codificacao_var = tk.StringVar(value="utf-8")
        self._criar_widgets()

    def _criar_widgets(self):
        config_geral_frame = ttk.LabelFrame(self, text="Configurações do Arquivo", padding="10")
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        entry_nome_arquivo = ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40)
        entry_nome_arquivo.grid(row=0, column=1, sticky="ew", padx=5)
        entry_nome_arquivo.bind("<FocusOut>", lambda e: self.app_controller.atualizar_titulo_aba(self))
        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, sticky="w", padx=5)
        Tooltip(entry_nome_arquivo, "Nome final do arquivo. O título da aba será atualizado.")
        ttk.Label(config_geral_frame, text="Linhas:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15).grid(row=0, column=3, sticky="ew",
                                                                                       padx=5)
        ttk.Label(config_geral_frame, text="Separador:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Combobox(config_geral_frame, textvariable=self.separador_var,
                     values=list(self.app_controller.separador_map.keys())).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Label(config_geral_frame, text="Codificação:").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Combobox(config_geral_frame, textvariable=self.codificacao_var,
                     values=["utf-8", "latin-1", "windows-1252", "utf-16"], state="readonly").grid(row=1, column=3,
                                                                                                   sticky="ew", padx=5)
        config_geral_frame.grid_columnconfigure(1, weight=1)
        config_geral_frame.grid_columnconfigure(3, weight=1)

        notebook_interno = ttk.Notebook(self)
        notebook_interno.pack(fill="both", expand=True, padx=10, pady=5)
        campos_tab, ordenacao_tab, unicidade_tab = ttk.Frame(notebook_interno), ttk.Frame(notebook_interno), ttk.Frame(
            notebook_interno)
        notebook_interno.add(campos_tab, text="Definição dos Campos")
        notebook_interno.add(ordenacao_tab, text="Ordenação")
        notebook_interno.add(unicidade_tab, text="Unicidade (Constraints)")

        ttk.Button(campos_tab, text="Adicionar Campo", command=self.adicionar_campo).pack(side="top", anchor="w",
                                                                                          pady=5, padx=5)
        canvas_frame = ttk.Frame(campos_tab)
        canvas_frame.pack(fill="both", expand=True, pady=5, padx=5)
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0)
        self.campos_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.campos_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        ttk.Button(ordenacao_tab, text="Adicionar Regra de Ordenação", command=self.adicionar_regra_sort).pack(
            side="top", anchor="w", pady=5, padx=5)
        self.sort_rules_frame = ttk.Frame(ordenacao_tab)
        self.sort_rules_frame.pack(side="top", fill="x", expand=True, pady=5, padx=5)

        ttk.Label(unicidade_tab, text="Selecione um ou mais campos que, juntos, devem ser únicos:",
                  wraplength=500).pack(anchor="w", padx=5, pady=5)
        self.constraint_listbox = tk.Listbox(unicidade_tab, selectmode="multiple", exportselection=False)
        self.constraint_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        Tooltip(self.constraint_listbox, "Use Ctrl+Click ou Shift+Click para selecionar múltiplos campos.")

    def _abrir_dialogo_condicional(self, campo_dict):
        """Abre a janela de diálogo para criar/editar uma regra condicional."""
        # A condição só pode se basear em campos que vêm ANTES do atual.
        campos_anteriores = [cf['nome'].get() for cf in self.frames_campos if cf['id'] < campo_dict['id']]
        if not campos_anteriores:
            messagebox.showinfo("Aviso",
                                "A condição depende de campos definidos anteriormente.\nMova este campo para baixo para poder adicionar uma condição.",
                                parent=self)
            return

        dialog = ConditionalRuleDialog(self, campos_anteriores, campo_dict['nome'].get(), campo_dict.get('condicional'))
        self.wait_window(dialog)

        if dialog.resultado is not None:
            campo_dict['condicional'] = dialog.resultado
            # Atualiza o estado visual do botão para indicar que há uma regra
            campo_dict['btn_condicao'].config(style="Accent.TButton")
        # Se o usuário cancelar, dialog.resultado será None e nada acontece.

    def adicionar_campo(self, config=None):
        config = config or {}
        frame_id = len(self.frames_campos)
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding=10)
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)

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
        fk_cardinalidade_var = tk.StringVar(value=config.get('cardinalidade', 'Um-para-Muitos (1:N)'))

        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w")
        entry_nome = ttk.Entry(campo_frame, textvariable=nome_var, width=15)
        entry_nome.grid(row=0, column=1, sticky="ew")
        entry_nome.bind("<FocusOut>", lambda e: self._atualizar_lista_unicidade())
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w")
        combo_tipo = ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12)
        combo_tipo.grid(row=0, column=3, sticky="ew")
        spin_rep = ttk.Spinbox(campo_frame, from_=0, to=999, textvariable=repeticao_var, width=5)
        check_pk = ttk.Checkbutton(campo_frame, text="É Chave Primária (PK)", variable=e_pk_var,
                                   command=lambda: (repeticao_var.set("1"), spin_rep.config(
                                       state="disabled")) if e_pk_var.get() else spin_rep.config(state="normal"))
        check_pk.grid(row=0, column=4, sticky="w", padx=5)
        ttk.Label(campo_frame, text="Repetir:").grid(row=1, column=4, sticky="w", pady=(5, 0))
        spin_rep.grid(row=1, column=5, sticky="w", pady=(5, 0))
        if e_pk_var.get(): spin_rep.config(state="disabled")
        action_buttons_frame = ttk.Frame(campo_frame)
        action_buttons_frame.grid(row=0, column=6, rowspan=2, padx=15)
        btn_subir = ttk.Button(action_buttons_frame, text="↑", width=3,
                               command=lambda fid=frame_id: self._mover_campo(fid, -1))
        btn_subir.pack(side="left")
        btn_descer = ttk.Button(action_buttons_frame, text="↓", width=3,
                                command=lambda fid=frame_id: self._mover_campo(fid, 1))
        btn_descer.pack(side="left")
        btn_remover = ttk.Button(action_buttons_frame, text="Remover",
                                 command=lambda index=frame_id: self.remover_campo(index))
        btn_remover.pack(side="left", padx=(5, 0))

        btn_condicao = ttk.Button(campo_frame, text="Adicionar Condição")
        btn_condicao.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")
        Tooltip(btn_condicao, "Adicionar uma regra para gerar este campo\ncom base no valor de um campo anterior.")
        if config and config.get('condicional'): btn_condicao.config(style="Accent.TButton")

        params_frame = ttk.Frame(campo_frame)
        params_frame.grid(row=2, column=0, columnspan=7, sticky='ew', pady=(10, 0))
        params_frame.grid_columnconfigure(1, weight=3)
        params_frame.grid_columnconfigure(2, weight=2)
        params_frame.grid_columnconfigure(3, weight=1)
        label_limites = ttk.Label(params_frame, text="Parâmetros:")
        entry_limite1, entry_limite2, entry_opcoes_regex = ttk.Entry(params_frame, textvariable=limite1_var), ttk.Entry(
            params_frame, textvariable=limite2_var), ttk.Entry(params_frame, textvariable=opcoes_var)
        combo_fk_arquivo, combo_fk_campo = ttk.Combobox(params_frame, textvariable=fk_arquivo_var,
                                                        state='readonly'), ttk.Combobox(params_frame,
                                                                                        textvariable=fk_campo_var,
                                                                                        state='readonly')
        combo_fk_cardinalidade = ttk.Combobox(params_frame, textvariable=fk_cardinalidade_var,
                                              values=["Um-para-Muitos (1:N)", "Um-para-Um (1:1)"], state='readonly')

        def _atualizar_parametros(*args):
            for widget in params_frame.winfo_children(): widget.grid_forget()
            tipo = tipo_var.get()
            label_limites.grid(row=0, column=0, sticky="w")
            if tipo in ['integer', 'float', 'string']:
                label_limites.config(text="Min/Max:")
                entry_limite1.grid(row=0, column=1,
                                   sticky="ew")
                entry_limite2.grid(row=0,
                                   column=2,
                                   sticky="ew")
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:")
                entry_limite1.grid(row=0, column=1,
                                   sticky="ew")
                entry_limite2.grid(
                    row=0, column=2, sticky="ew")
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções (,):")
                entry_opcoes_regex.config(
                    textvariable=opcoes_var)
                entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=3)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:")
                entry_opcoes_regex.config(
                    textvariable=regex_var)
                entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=3)
            elif tipo == 'chave_estrangeira':
                label_limites.config(text="Relação:")
                arquivos_e_pks = self.app_controller.get_lista_de_abas_e_pks(aba_atual=self)
                combo_fk_arquivo['values'] = list(arquivos_e_pks.keys())
                combo_fk_arquivo.grid(row=0, column=1, sticky="ew")
                combo_fk_campo.grid(row=0, column=2, sticky="ew")
                combo_fk_cardinalidade.grid(row=0, column=3, sticky="ew", padx=(5, 0))

                def on_fk_arquivo_selecionado(event):
                    fk_campo_var.set('')
                    combo_fk_campo['values'] = arquivos_e_pks.get(fk_arquivo_var.get(), [])

                combo_fk_arquivo.bind("<<ComboboxSelected>>", on_fk_arquivo_selecionado)
                if fk_arquivo_var.get(): on_fk_arquivo_selecionado(None)

        tipo_var.trace_add("write", _atualizar_parametros)
        _atualizar_parametros()

        campo_dict = {'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var, 'e_pk': e_pk_var,
                      'repeticao': repeticao_var, 'limite1': limite1_var, 'limite2': limite2_var, 'opcoes': opcoes_var,
                      'regex': regex_var, 'fk_arquivo': fk_arquivo_var, 'fk_campo': fk_campo_var,
                      'fk_cardinalidade': fk_cardinalidade_var, 'btn_subir': btn_subir, 'btn_descer': btn_descer,
                      'btn_remover': btn_remover, 'btn_condicao': btn_condicao,
                      'condicional': config.get('condicional')}
        btn_condicao.config(command=lambda c=campo_dict: self._abrir_dialogo_condicional(c))
        self.frames_campos.append(campo_dict)
        self._atualizar_lista_unicidade()
        self.app_controller.after_idle(lambda: self.app_controller._update_scrollregion(self.canvas))

    def _atualizar_lista_unicidade(self):
        selecao_previa = self.constraint_listbox.curselection()
        nomes_selecionados = {self.constraint_listbox.get(i) for i in selecao_previa}
        self.constraint_listbox.delete(0, tk.END)
        novos_nomes = [campo_dict['nome'].get() for campo_dict in self.frames_campos]
        for nome in novos_nomes: self.constraint_listbox.insert(tk.END, nome)
        for i, nome in enumerate(novos_nomes):
            if nome in nomes_selecionados: self.constraint_listbox.selection_set(i)

    def _atualizar_comandos_e_titulos(self):
        self._atualizar_nomes_campos_ordenacao()
        self._atualizar_lista_unicidade()
        for i, campo_dict in enumerate(self.frames_campos):
            campo_dict['id'] = i
            campo_dict['frame'].config(text=f"Campo {i + 1}")
            campo_dict['btn_subir'].config(command=lambda index=i: self._mover_campo(index, -1))
            campo_dict['btn_descer'].config(command=lambda index=i: self._mover_campo(index, 1))
            campo_dict['btn_remover'].config(command=lambda index=i: self.remover_campo(index))

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
                if isinstance(widget, ttk.Combobox): widget['values'] = nomes_campos
                break

    def adicionar_regra_sort(self, config=None):
        config = config or {}
        rule_id = len(self.frames_sort)
        rule_frame = ttk.Frame(self.sort_rules_frame)
        rule_frame.pack(fill="x", pady=2)
        nomes_campos = [f['nome'].get() for f in self.frames_campos if f['nome'].get()]
        campo_var = tk.StringVar(value=config.get('campo', ''))
        ordem_var = tk.StringVar(value=config.get('ordem', 'Ascendente'))
        ttk.Label(rule_frame, text="Ordenar por:").pack(side="left")
        ttk.Combobox(rule_frame, textvariable=campo_var, values=nomes_campos, state="readonly", width=30).pack(
            side="left", padx=5)
        ttk.Combobox(rule_frame, textvariable=ordem_var, values=["Ascendente", "Descendente"], state="readonly",
                     width=15).pack(side="left", padx=5)
        ttk.Button(rule_frame, text="Remover", command=lambda: self.remover_regra_sort(rule_id)).pack(side="left",
                                                                                                      padx=5)
        self.frames_sort.append({'frame': rule_frame, 'id': rule_id, 'campo': campo_var, 'ordem': ordem_var})

    def remover_regra_sort(self, rule_id):
        for r in self.frames_sort:
            if r['id'] == rule_id: r['frame'].destroy()
            self.frames_sort.remove(r)
            break
        for i, r in enumerate(self.frames_sort): r['id'] = i

    def coletar_config_aba(self):
        config_aba = {"nome_arquivo": self.nome_arquivo_var.get(), "num_linhas": int(self.num_linhas_var.get()),
                      "separador": self.app_controller.separador_map.get(self.separador_var.get(),
                                                                         self.separador_var.get()),
                      "codificacao": self.codificacao_var.get(), "campos": [], "regras_sort": [],
                      "constraint_unicidade": []}
        for widgets in self.frames_campos:
            campo_cfg = {"nome": widgets['nome'].get(), "tipo": widgets['tipo'].get(), "e_pk": widgets['e_pk'].get(),
                         "repeticao": int(widgets['repeticao'].get())}
            if widgets.get('condicional'): campo_cfg['condicional'] = widgets['condicional']
            tipo = widgets['tipo'].get()
            if tipo in ['integer', 'float', 'string', 'datetime']:
                campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
            elif tipo == 'lista_opcoes':
                campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
            elif tipo == 'regex':
                campo_cfg['regex_pattern'] = widgets['regex'].get()
            elif tipo == 'chave_estrangeira':
                campo_cfg['fk_arquivo'] = widgets['fk_arquivo'].get()
                campo_cfg['fk_campo'] = widgets[
                    'fk_campo'].get()
                campo_cfg['cardinalidade'] = widgets['fk_cardinalidade'].get()
            config_aba["campos"].append(campo_cfg)
        for rule_widgets in self.frames_sort: config_aba["regras_sort"].append(
            {'campo': rule_widgets['campo'].get(), 'ordem': rule_widgets['ordem'].get()})
        indices_selecionados = self.constraint_listbox.curselection()
        config_aba["constraint_unicidade"] = [self.constraint_listbox.get(i) for i in indices_selecionados]
        return config_aba

    def carregar_config(self, config):
        self.nome_arquivo_var.set(config.get("nome_arquivo", ""))
        self.num_linhas_var.set(str(config.get("num_linhas", 100)))
        self.codificacao_var.set(config.get("codificacao", "utf-8"))
        separador_salvo = config.get("separador", ",")
        self.separador_var.set(
            {v: k for k, v in self.app_controller.separador_map.items()}.get(separador_salvo, separador_salvo))
        for campo_config in config.get("campos", []): self.adicionar_campo(campo_config)
        for sort_config in config.get("regras_sort", []): self.adicionar_regra_sort(sort_config)
        campos_constraint = config.get("constraint_unicidade", [])
        for i, nome_campo in enumerate(self.constraint_listbox.get(0, tk.END)):
            if nome_campo in campos_constraint: self.constraint_listbox.selection_set(i)
