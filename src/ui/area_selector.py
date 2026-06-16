import tkinter as tk
from typing import Optional, Tuple, Any

from src.core.config import guardar_configuracion


class AreaSelector:
    """Clase encargada de proveer la interfaz de calibración visual de sectores.

    Crea un canvas semitransparente sobre la pantalla completa para permitirle al
    usuario delimitar arrastrando el mouse las tres zonas de interés en AX:
    Sector A (Checkboxes), Sector B (Menú de registro) y Sector Scroll.
    """

    def __init__(self) -> None:
        """Inicializa la ventana de calibración y enlaza los eventos del mouse."""
        self.root: tk.Tk = tk.Tk()
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(background='black')
        self.root.config(cursor="cross")

        self.canvas: tk.Canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.rect: Optional[Any] = None
        self.sector_a: Optional[Tuple[int, int, int, int]] = None
        self.sector_b: Optional[Tuple[int, int, int, int]] = None
        self.sector_scroll: Optional[Tuple[int, int, int, int]] = None
        self.current_sector: str = "A"

        self.instruction_text: Any = self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 50, 
            text="1. Selecciona el SECTOR A (Cuadrado de Checkboxes)", 
            fill="white", font=("Arial", 24, "bold")
        )

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_button_press(self, event: tk.Event) -> None:
        """Maneja el evento de presión inicial del botón izquierdo del mouse.

        Args:
            event (tk.Event): Evento de Tkinter con las coordenadas de click.
        """
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        
        # Colores distintivos por sector
        color: str = "red" if self.current_sector == "A" else ("blue" if self.current_sector == "B" else "yellow")
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline=color, width=3)

    def on_move_press(self, event: tk.Event) -> None:
        """Maneja el movimiento del mouse mientras se mantiene presionado el botón.

        Args:
            event (tk.Event): Evento de arrastre con las coordenadas actuales.
        """
        cur_x: int = event.x
        cur_y: int = event.y
        if self.rect and self.start_x is not None and self.start_y is not None:
            self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event: tk.Event) -> None:
        """Maneja la liberación del botón del mouse guardando la zona capturada.

        Args:
            event (tk.Event): Evento de liberación con las coordenadas finales.
        """
        if self.start_x is None or self.start_y is None:
            return
            
        end_x: int = event.x
        end_y: int = event.y
        
        left: int = min(self.start_x, end_x)
        top: int = min(self.start_y, end_y)
        width: int = abs(self.start_x - end_x)
        height: int = abs(self.start_y - end_y)

        area: Tuple[int, int, int, int] = (left, top, width, height)

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
            if self.sector_a and self.sector_b:
                guardar_configuracion(list(self.sector_a), list(self.sector_b), list(self.sector_scroll))
            print("Configuración guardada.")
            print("Puedes ajustar el offset OCR (ocr_region_offset) en config_sectores.json")
            print("  si los IDs de diario no se leen correctamente.")
            self.root.destroy()

    def run(self) -> None:
        """Inicia el loop principal de visualización del calibrador."""
        self.root.mainloop()


if __name__ == "__main__":
    print("Iniciando selector de áreas...")
    app = AreaSelector()
    app.run()
