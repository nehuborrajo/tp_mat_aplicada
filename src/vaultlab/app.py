"""Punto de entrada sin efectos gráficos durante la importación."""


def main() -> None:
    """Crea la ventana y ejecuta el bucle gráfico en el hilo principal."""
    from vaultlab.ui.main_window import create_window

    window = create_window()
    window.mainloop()
