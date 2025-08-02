# app_gui.py
# Camada de Apresentação e Controle: com a correção do método grid_columnconfigure.

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue

# Importa as funcionalidades dos outros módulos
from utils import Tooltip
from data_generator import run_generation_in_thread


class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Dados v3.2.1 (Hotfix)")
        self.geometry("950x800")

        self.result_queue = queue.Queue()
        self.separador_map = {"Vírgula (,)": ",", "Ponto e Vírgula (;)": ";", "Tab (    )": "\t", "Pipe (|)": "|"}
        self.frames_campos, self.frames_sort = [], []
        self._criar_widgets()

    def _criar_widgets(self):
        main_frame = ttk.Frame(self);
        main_frame.pack(fill="both", expand=True)

        control_frame = ttk.Frame(main_frame, padding="10");
        control_frame.pack(side="top", fill="x", expand=False)
        ttk.Button(control_frame, text="Carregar Configuração", command=self.carregar_configuracao).pack(side="left",
                                                                                                         padx=5)
        ttk.Button(control_frame, text="Salvar Configuração", command=self.salvar_configuracao).pack(side="left",
                                                                                                     padx=5)
        ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_sessao).pack(side="left", padx=5)

        config_geral_frame = ttk.LabelFrame(main_frame, text="Configurações Gerais", padding="10");
        config_geral_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        self.nome_arquivo_var = tk.StringVar(value="massa_de_dados.csv")
        self.num_linhas_var = tk.StringVar(value="100")
        self.separador_var = tk.StringVar(value="Vírgula (,)")
        self.codificacao_var = tk.StringVar(value="utf-8")

        ttk.Label(config_geral_frame, text="Nome do Arquivo CSV:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(config_geral_frame, textvariable=self.nome_arquivo_var, width=40).grid(row=0, column=1, sticky="ew",
                                                                                         padx=5, pady=2)
        ttk.Label(config_geral_frame, text="Quantidade de Linhas:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Entry(config_geral_frame, textvariable=self.num_linhas_var, width=15).grid(row=0, column=3, sticky="ew",
                                                                                       padx=5, pady=2)
        ttk.Label(config_geral_frame, text="Separador:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Combobox(config_geral_frame, textvariable=self.separador_var, values=list(self.separador_map.keys())).grid(
            row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(config_geral_frame, text="Codificação:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Combobox(config_geral_frame, textvariable=self.codificacao_var,
                     values=["utf-8", "latin-1", "windows-1252", "utf-16"], state="readonly").grid(row=1, column=3,
                                                                                                   sticky="ew", padx=5,
                                                                                                   pady=2)

        # <<< CORREÇÃO AQUI: 'grid_column_configure' para 'grid_columnconfigure' >>>
        config_geral_frame.grid_columnconfigure(1, weight=1)
        config_geral_frame.grid_columnconfigure(3, weight=1)

        campos_container = ttk.LabelFrame(main_frame, text="Definição dos Campos", padding="10");
        campos_container.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))
        ttk.Button(campos_container, text="Adicionar Campo", command=self.adicionar_campo).pack(side="top", anchor="w",
                                                                                                pady=5)
        canvas_frame = ttk.Frame(campos_container);
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0);
        self.campos_frame = ttk.Frame(self.canvas);
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview);
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y");
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.campos_frame, anchor="nw");
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        sort_frame = ttk.LabelFrame(main_frame, text="Configurações de Ordenação", padding="10");
        sort_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        ttk.Button(sort_frame, text="Adicionar Regra", command=self.adicionar_regra_sort).pack(side="top", anchor="w")
        self.sort_warning_label = ttk.Label(sort_frame, text="Aviso: Ordenação ativa consome mais memória.",
                                            foreground="orange")
        self.sort_rules_frame = ttk.Frame(sort_frame);
        self.sort_rules_frame.pack(side="top", fill="x", expand=True, pady=5)

        action_frame = ttk.Frame(main_frame, padding="10");
        action_frame.pack(side="bottom", fill="x", expand=False)
        self.btn_gerar = ttk.Button(action_frame, text="Gerar Dados", command=self.iniciar_geracao,
                                    style="Accent.TButton");
        self.btn_gerar.pack()

        try:
            self.tk.call("source", "azure.tcl"); self.tk.call("set_theme", "light")
        except tk.TclError:
            pass
        self.adicionar_campo()

    def iniciar_geracao(self):
        config = self._coletar_configuracoes()
        if not config: return
        self.btn_gerar.config(state="disabled", text="Gerando...")
        thread = threading.Thread(target=run_generation_in_thread, args=(config, self.result_queue), daemon=True)
        thread.start()
        self.after(100, self.verificar_thread)

    def verificar_thread(self):
        try:
            result = self.result_queue.get_nowait()
            self.btn_gerar.config(state="normal", text="Gerar Dados")
            if result['status'] == 'success':
                messagebox.showinfo("Sucesso", result['message'])
            else:
                messagebox.showerror("Erro na Geração", result['message'])
        except queue.Empty:
            self.after(100, self.verificar_thread)

    # O resto do arquivo permanece o mesmo da versão anterior.
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width); self.after_idle(self._update_scrollregion)

    def _update_scrollregion(self):
        self.canvas.update_idletasks(); self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def adicionar_campo(self, config=None):
        config = config or {};
        frame_id = len(self.frames_campos);
        campo_frame = ttk.LabelFrame(self.campos_frame, text=f"Campo {frame_id + 1}", padding=10);
        campo_frame.pack(fill="x", expand=True, padx=5, pady=5)
        nome_var = tk.StringVar(value=config.get('nome', f'campo_{frame_id + 1}'));
        tipos = ['integer', 'float', 'string', 'nome_pessoa', 'boolean', 'datetime', 'uuid', 'lista_opcoes', 'regex'];
        tipo_var = tk.StringVar(value=config.get('tipo', 'string'));
        repeticao_var = tk.StringVar(value=str(config.get('repeticao', '0')))
        ttk.Label(campo_frame, text="Nome:").grid(row=0, column=0, sticky="w");
        ttk.Entry(campo_frame, textvariable=nome_var, width=20).grid(row=0, column=1, sticky="ew")
        ttk.Label(campo_frame, text="Tipo:").grid(row=0, column=2, sticky="w");
        ttk.Combobox(campo_frame, textvariable=tipo_var, values=tipos, state="readonly", width=12).grid(row=0, column=3,
                                                                                                        sticky="ew")
        ttk.Label(campo_frame, text="Repetir:").grid(row=0, column=4, sticky="w");
        ttk.Spinbox(campo_frame, from_=0, to=999, textvariable=repeticao_var, width=5).grid(row=0, column=5, sticky="w")
        action_buttons_frame = ttk.Frame(campo_frame);
        action_buttons_frame.grid(row=0, column=6, padx=15)
        ttk.Button(action_buttons_frame, text="↑", width=3,
                   command=lambda fid=frame_id: self._mover_campo(fid, -1)).pack(side="left")
        ttk.Button(action_buttons_frame, text="↓", width=3,
                   command=lambda fid=frame_id: self._mover_campo(fid, 1)).pack(side="left")
        ttk.Button(action_buttons_frame, text="Remover", command=lambda index=frame_id: self.remover_campo(index)).pack(
            side="left", padx=(5, 0))
        label_limites = ttk.Label(campo_frame, text="Parâmetros:");
        label_limites.grid(row=1, column=0, sticky="w")
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
                label_limites.config(text="Min/Max:");entry_limite1.grid(row=1, column=1,
                                                                         sticky="ew");entry_limite2.grid(row=1,
                                                                                                         column=2,
                                                                                                         sticky="ew",
                                                                                                         columnspan=2)
            elif tipo == 'datetime':
                label_limites.config(text="Data Início/Fim:");entry_limite1.grid(row=1, column=1,
                                                                                 sticky="ew");entry_limite2.grid(row=1,
                                                                                                                 column=2,
                                                                                                                 sticky="ew",
                                                                                                                 columnspan=2)
            elif tipo == 'lista_opcoes':
                label_limites.config(text="Opções:");entry_opcoes_regex.config(
                    textvariable=opcoes_var);entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4)
            elif tipo == 'regex':
                label_limites.config(text="Padrão Regex:");entry_opcoes_regex.config(
                    textvariable=regex_var);entry_opcoes_regex.grid(row=1, column=1, sticky="ew", columnspan=4)

        tipo_var.trace_add("write", _atualizar_parametros);
        _atualizar_parametros()
        self.frames_campos.append(
            {'frame': campo_frame, 'id': frame_id, 'nome': nome_var, 'tipo': tipo_var, 'repeticao': repeticao_var,
             'limite1': limite1_var, 'limite2': limite2_var, 'opcoes': opcoes_var, 'regex': regex_var})
        self.after_idle(self._update_scrollregion)

    def _atualizar_comandos_e_titulos(self):
        self._atualizar_nomes_campos_ordenacao()
        for i, campo_dict in enumerate(self.frames_campos):
            campo_dict['id'] = i
            campo_dict['frame'].config(text=f"Campo {i + 1}")
            # Procura o frame de ações que contém os botões
            for child in campo_dict['frame'].winfo_children():
                if isinstance(child, ttk.Frame):
                    action_frame = child
                    buttons = action_frame.winfo_children()
                    if len(buttons) == 3:  # Verifica se temos os 3 botões esperados
                        btn_subir, btn_descer, btn_remover = buttons
                        btn_subir.config(command=lambda index=i: self._mover_campo(index, -1))
                        btn_descer.config(command=lambda index=i: self._mover_campo(index, 1))
                        btn_remover.config(command=lambda index=i: self.remover_campo(index))

    def _redesenhar_layout_campos(self):
        for campo_dict in self.frames_campos: campo_dict['frame'].pack_forget()
        for campo_dict in self.frames_campos: campo_dict['frame'].pack(fill="x", expand=True, padx=5, pady=5)
        self.after_idle(self._update_scrollregion)

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
        for rule_dict in self.frames_sort: rule_dict['frame'].winfo_children()[1]['values'] = nomes_campos

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
        self.sort_warning_label.pack(side="top", anchor="w", pady=(5, 0))

    def remover_regra_sort(self, rule_id):
        for rule_dict in self.frames_sort:
            if rule_dict['id'] == rule_id: rule_dict['frame'].destroy(); self.frames_sort.remove(rule_dict); break
        for i, rule_dict in enumerate(self.frames_sort): rule_dict['id'] = i
        if not self.frames_sort: self.sort_warning_label.pack_forget()

    def _coletar_configuracoes(self):
        try:
            config = {"nome_arquivo": self.nome_arquivo_var.get(), "num_linhas": int(self.num_linhas_var.get()),
                      "separador": self.separador_map.get(self.separador_var.get(), self.separador_var.get()),
                      "codificacao": self.codificacao_var.get(), "campos": [], "regras_sort": []}
            if not self.frames_campos: messagebox.showwarning("Aviso", "Nenhum campo foi adicionado."); return None
            for widgets in self.frames_campos:
                tipo = widgets['tipo'].get();
                campo_cfg = {"nome": widgets['nome'].get(), "tipo": tipo, "repeticao": int(widgets['repeticao'].get())}
                if tipo in ['integer', 'float', 'string', 'datetime']:
                    campo_cfg['limite'] = (widgets['limite1'].get(), widgets['limite2'].get())
                elif tipo == 'lista_opcoes':
                    campo_cfg['opcoes'] = [opt.strip() for opt in widgets['opcoes'].get().split(',') if opt.strip()]
                elif tipo == 'regex':
                    campo_cfg['regex_pattern'] = widgets['regex'].get()
                config["campos"].append(campo_cfg)
            for rule_widgets in self.frames_sort: config["regras_sort"].append(
                {'campo': rule_widgets['campo'].get(), 'ordem': rule_widgets['ordem'].get()})
            return config
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Verifique se os números são válidos."); return None

    def carregar_configuracao(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.limpar_sessao(confirmar=False)
            self.nome_arquivo_var.set(config.get("nome_arquivo", "dados.csv"));
            self.num_linhas_var.set(str(config.get("num_linhas", 100)));
            self.codificacao_var.set(config.get("codificacao", "utf-8"))
            separador_salvo = config.get("separador", ",");
            self.separador_var.set({v: k for k, v in self.separador_map.items()}.get(separador_salvo, separador_salvo))
            for campo_config in config.get("campos", []): self.adicionar_campo(campo_config)
            for sort_config in config.get("regras_sort", []): self.adicionar_regra_sort(sort_config)
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Não foi possível ler o arquivo:\n{e}")

    def limpar_sessao(self, confirmar=True):
        if confirmar and not messagebox.askyesno("Confirmar", "Deseja limpar tudo?"): return
        self.nome_arquivo_var.set("massa_de_dados.csv");
        self.num_linhas_var.set("100");
        self.separador_var.set("Vírgula (,)");
        self.codificacao_var.set("utf-8")
        for campo_dict in list(self.frames_campos): campo_dict['frame'].destroy()
        self.frames_campos.clear()
        for sort_dict in list(self.frames_sort): sort_dict['frame'].destroy()
        self.frames_sort.clear()
        self.sort_warning_label.pack_forget()
        self.adicionar_campo()

    def salvar_configuracao(self):
        config = self._coletar_configuracoes()
        if not config: return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Sucesso", f"Configuração salva em {filepath}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo: {e}")