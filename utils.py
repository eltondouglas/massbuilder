# utils.py
# Contém classes auxiliares e constantes usadas em toda a aplicação.

import tkinter as tk

# --- LISTAS DE NOMES BRASILEIROS ---
LISTA_NOMES = [
    'Miguel', 'Arthur', 'Gael', 'Heitor', 'Theo', 'Davi', 'Gabriel', 'Bernardo', 'Samuel', 'João',
    'Helena', 'Alice', 'Laura', 'Maria Alice', 'Sophia', 'Manuela', 'Maitê', 'Liz', 'Cecília', 'Isabella',
    'Lucas', 'Pedro', 'Guilherme', 'Matheus', 'Rafael', 'Enzo', 'Nicolas', 'Lorenzo', 'Gustavo', 'Felipe',
    'Júlia', 'Beatriz', 'Mariana', 'Lívia', 'Giovanna', 'Yasmin', 'Isadora', 'Clara', 'Valentina', 'Heloísa'
]
LISTA_SOBRENOMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes',
    'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa',
    'Rocha', 'Dias', 'Nunes', 'Mendes', 'Moura', 'Cardoso', 'Teixeira', 'Correia', 'Melo', 'Araújo'
]


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

        label = tk.Label(
            self.tooltip_window, text=self.text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            font=("tahoma", "8", "normal")
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None