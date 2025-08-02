# ui/main_window.py
# Módulo que define a classe AppGeradorDados, a janela principal da aplicação.

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue

from ui.file_tab import FileTab  # Importa a classe da aba
from data_generator import run_generation_in_thread


class AppGeradorDados(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Dados v5.0 (Arquitetura Modular)")
        self.geometry("1024x768")
        icon = tk.PhotoImage(file="images/massbuilder.png")
        self.iconphoto(False, icon)
        self.result_queue = queue.Queue()
        self.separador_map = {"Vírgula (,)": ",", "Ponto e Vírgula (;)": ";", "Tab (    )": "\t", "Pipe (|)": "|"}
        self.tabs = []
        self._criar_widgets()

    def _criar_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(side="top", fill="x", expand=False)
        ttk.Button(control_frame, text="Carregar Sessão", command=self.carregar_sessao).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Salvar Sessão", command=self.salvar_sessao).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Limpar Tudo", command=self.limpar_tudo).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Adicionar Arquivo", command=self.adicionar_aba).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Remover Arquivo Atual", command=self.remover_aba_atual).pack(side="left",
                                                                                                     padx=5)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(side="bottom", fill="x", expand=False)
        self.btn_gerar = ttk.Button(action_frame, text="Gerar Todos os Arquivos", command=self.iniciar_geracao,
                                    style="Accent.TButton")
        self.btn_gerar.pack()

        try:
            self.tk.call("source", "azure.tcl"); self.tk.call("set_theme", "light")
        except tk.TclError:
            pass
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
            selected_widget = self.nametowidget(self.notebook.select())
            self.tabs.remove(selected_widget)
            self.notebook.forget(selected_widget)
        else:
            messagebox.showwarning("Aviso", "Não é possível remover o último arquivo.")

    def atualizar_titulo_aba(self, tab_widget):
        self.notebook.tab(tab_widget, text=tab_widget.nome_arquivo_var.get())

    def get_lista_de_abas_e_pks(self, aba_atual=None):
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
        self.btn_gerar.config(state="disabled", text="Gerando...")
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
        if confirmar and not messagebox.askyesno("Confirmar", "Deseja limpar toda a sessão?"): return
        for tab_widget in list(self.tabs): self.notebook.forget(tab_widget)
        self.tabs.clear()
        self.adicionar_aba()