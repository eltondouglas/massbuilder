# ui/file_tab.py
# Módulo que define a classe FileTab, o componente responsável por uma única aba da interface.

import tkinter as tk
from tkinter import ttk
from utils import Tooltip


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

    def adicionar_campo(self, config=None):
        config = config or {}
        frame_id = len(self.frames_campos)
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding=10)
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)

        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'));
        tipos = ['integer', 'float', 'string', 'nome_pessoa', 'boolean', 'datetime', 'uuid', 'lista_opcoes', 'regex',
                 'chave_estrangeira'];
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'));
        e_pk_var = tk.BooleanVar(value=config.get('e_pk', False));
        repeticao_var = tk.StringVar(value=str(config.get('repeticao', '0')));
        limite1_var = tk.StringVar(value=str(config.get('limite', ['', ''])[0]));
        limite2_var = tk.StringVar(value=str(config.get('limite', ['', ''])[1]));
        opcoes_var = tk.StringVar(value=", ".join(config.get('opcoes', [])));
        regex_var = tk.StringVar(value=config.get('regex_pattern', ''));
        fk_arquivo_var = tk.StringVar(value=config.get('fk_arquivo', ''));
        fk_campo_var = tk.StringVar(value=config.get('fk_campo', ''));
        fk_cardinalidade_var = tk.StringVar(value=config.get('cardinalidade', 'Um-para-Muitos (1:N)'))

        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w")
        entry_nome = ttk.Entry(campo_frame, textvariable=nome_var, width=15)
        entry_nome.grid(row=0, column=1, sticky="ew")
        entry_nome.bind("<FocusOut>", lambda e: self._atualizar_lista_unicidade())

        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12).grid(row=0, column=3,
                                                                                                        sticky="ew")
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

        params_frame = ttk.Frame(campo_frame);
        params_frame.grid(row=2, column=0, columnspan=7, sticky='ew', pady=(10, 0));
        params_frame.grid_columnconfigure(1, weight=3);
        params_frame.grid_columnconfigure(2, weight=2);
        params_frame.grid_columnconfigure(3, weight=1)
        label_limites = ttk.Label(params_frame, text="Parâmetros:");
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
            tipo = tipo_var.get();
            label_limites.grid(row=0, column=0, sticky="w")
            if tipo in ['integer', 'float', 'string']:
                label_limites.config(text="Min/Max:"); entry_limite1.grid(row=0, column=1,
                                                                          sticky="ew"); entry_limite2.grid(row=0,
                                                                                                           column=2,
                                                                                                           sticky="ew")
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:"); entry_limite1.grid(row=0, column=1,
                                                                                  sticky="ew"); entry_limite2.grid(
                    row=0, column=2, sticky="ew")
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções (,):"); entry_opcoes_regex.config(
                    textvariable=opcoes_var); entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=3)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:"); entry_opcoes_regex.config(
                    textvariable=regex_var); entry_opcoes_regex.grid(row=0, column=1, sticky="ew", columnspan=3)
            elif tipo == 'chave_estrangeira':
                label_limites.config(text="Relação:");
                arquivos_e_pks = self.app_controller.get_lista_de_abas_e_pks(aba_atual=self);
                combo_fk_arquivo['values'] = list(arquivos_e_pks.keys());
                combo_fk_arquivo.grid(row=0, column=1, sticky="ew");
                combo_fk_campo.grid(row=0, column=2, sticky="ew");
                combo_fk_cardinalidade.grid(row=0, column=3, sticky="ew", padx=(5, 0))

                def on_fk_arquivo_selecionado(event):
                    fk_campo_var.set(''); combo_fk_campo['values'] = arquivos_e_pks.get(fk_arquivo_var.get(), [])

                combo_fk_arquivo.bind("<<ComboboxSelected>>", on_fk_arquivo_selecionado)
                if fk_arquivo_var.get(): on_fk_arquivo_selecionado(None)

        tipo_var.trace_add("write", _atualizar_parametros);
        _atualizar_parametros()

        self.frames_campos.append({
            'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var, 'e_pk': e_pk_var,
            'repeticao': repeticao_var, 'limite1': limite1_var, 'limite2': limite2_var,
            'opcoes': opcoes_var, 'regex': regex_var, 'fk_arquivo': fk_arquivo_var,
            'fk_campo': fk_campo_var, 'fk_cardinalidade': fk_cardinalidade_var,
            'btn_subir': btn_subir, 'btn_descer': btn_descer, 'btn_remover': btn_remover
        })
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
                if isinstance(widget, ttk.Combobox): widget['values'] = nomes_campos; break

    def adicionar_regra_sort(self, config=None):
        config = config or {};
        rule_id = len(self.frames_sort);
        rule_frame = ttk.Frame(self.sort_rules_frame);
        rule_frame.pack(fill="x", pady=2)
        nomes_campos = [f['nome'].get() for f in self.frames_campos if f['nome'].get()];
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
        for r in self.frames_sort:
            if r['id'] == rule_id: r['frame'].destroy();self.frames_sort.remove(r);break
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
            tipo = widgets['tipo'].get()
            if tipo in ['integer', 'float', 'string', 'datetime']:
                campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
            elif tipo == 'lista_opcoes':
                campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
            elif tipo == 'regex':
                campo_cfg['regex_pattern'] = widgets['regex'].get()
            elif tipo == 'chave_estrangeira':
                campo_cfg['fk_arquivo'] = widgets['fk_arquivo'].get(); campo_cfg['fk_campo'] = widgets[
                    'fk_campo'].get(); campo_cfg['cardinalidade'] = widgets['fk_cardinalidade'].get()
            config_aba["campos"].append(campo_cfg)
        for rule_widgets in self.frames_sort: config_aba["regras_sort"].append(
            {'campo': rule_widgets['campo'].get(), 'ordem': rule_widgets['ordem'].get()})
        indices_selecionados = self.constraint_listbox.curselection()
        config_aba["constraint_unicidade"] = [self.constraint_listbox.get(i) for i in indices_selecionados]
        return config_aba

    def carregar_config(self, config):
        self.nome_arquivo_var.set(config.get("nome_arquivo", ""));
        self.num_linhas_var.set(str(config.get("num_linhas", 100)));
        self.codificacao_var.set(config.get("codificacao", "utf-8"))
        separador_salvo = config.get("separador", ",");
        self.separador_var.set(
            {v: k for k, v in self.app_controller.separador_map.items()}.get(separador_salvo, separador_salvo))
        for campo_config in config.get("campos", []): self.adicionar_campo(campo_config)
        for sort_config in config.get("regras_sort", []): self.adicionar_regra_sort(sort_config)
        campos_constraint = config.get("constraint_unicidade", [])
        for i, nome_campo in enumerate(self.constraint_listbox.get(0, tk.END)):
            if nome_campo in campos_constraint: self.constraint_listbox.selection_set(i)