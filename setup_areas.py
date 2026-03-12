import tkinter as tk
from config import guardar_configuracion

class AreaSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(background='black')
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None
        self.sector_a = None
        self.sector_b = None
        self.sector_scroll = None
        self.current_sector = "A"

        self.instruction_text = self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 50, 
            text="1. Selecciona el SECTOR A (Cuadrado de Checkboxes)", 
            fill="white", font=("Arial", 24, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        
        # Colores por sector
        color = "red" if self.current_sector == "A" else ("blue" if self.current_sector == "B" else "yellow")
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline=color, width=3)

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(self.start_x - end_x)
        height = abs(self.start_y - end_y)

        area = (left, top, width, height)

        if self.current_sector == "A":
            self.sector_a = area
            self.current_sector = "B"
            self.canvas.itemconfig(self.instruction_text, text="2. Selecciona el SECTOR B (Barra superior de Botones)")
            self.rect = None
        elif self.current_sector == "B":
            self.sector_b = area
            self.current_sector = "C"
            self.canvas.itemconfig(self.instruction_text, text="3. Selecciona el SECTOR SCROLL (Pequeño recuadro sobre la flecha de abajo)")
            self.rect = None
        elif self.current_sector == "C":
            self.sector_scroll = area
            guardar_configuracion(self.sector_a, self.sector_b, self.sector_scroll)
            self.root.destroy()
            print("Configuración finalizada con éxito.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("Iniciando selector de áreas...")
    app = AreaSelector()
    app.run()
