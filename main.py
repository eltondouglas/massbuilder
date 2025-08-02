# main.py
# Ponto de entrada principal da aplicação.

from app_gui import AppGeradorDados

if __name__ == "__main__":
    try:
        app = AppGeradorDados()
        app.mainloop()
    except Exception as e:
        # Um último recurso para capturar erros inesperados na inicialização.
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        print(e)
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro crítico ao iniciar a aplicação:\n{e}")