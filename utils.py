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
        self.scheduled_id = None
        # Usar Motion em vez de Enter para evitar múltiplas chamadas
        self.widget.bind("<Motion>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        # Garantir que o tooltip seja destruído quando o widget for destruído
        self.widget.bind("<Destroy>", self.hide_tooltip)
    
    def schedule_tooltip(self, event):
        # Cancelar qualquer exibição agendada anterior
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
            
        # Agendar a exibição com um pequeno atraso para evitar flickering
        if not self.tooltip_window:
            self.scheduled_id = self.widget.after(500, lambda: self.show_tooltip(event))
    
    def show_tooltip(self, event):
        self.scheduled_id = None
        if self.tooltip_window or not self.text:
            return

        # Posicionar o tooltip abaixo do cursor para melhor experiência do usuário
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 10

        # Criar o tooltip apenas uma vez e reutilizá-lo
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Configurar para ficar acima de outras janelas
        self.tooltip_window.attributes("-topmost", True)

        label = tk.Label(
            self.tooltip_window, text=self.text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            font=("tahoma", "8", "normal")
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        # Cancelar qualquer exibição agendada
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
            
        # Destruir a janela do tooltip
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None