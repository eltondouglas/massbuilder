# main.py
# Ponto de entrada principal da aplicação. Agora importa da nova estrutura 'ui'.

import tkinter as tk
from tkinter import messagebox
from ui.main_window import AppGeradorDados

if __name__ == "__main__":
    try:
        app = AppGeradorDados()
        app.mainloop()
    except Exception as e:
        # Captura erros críticos na inicialização
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro crítico ao iniciar a aplicação:\n{e}")