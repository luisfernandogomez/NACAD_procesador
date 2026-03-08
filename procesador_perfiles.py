from pathlib import Path
import numpy as np
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt


def select_file():
    """
    Abre una ventana para seleccionar el archivo TXT del perfil.
    """
    root = tk.Tk()
    root.withdraw()
    root.update()

    file_path = filedialog.askopenfilename(
        title="Selecciona el archivo del perfil",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )

    root.destroy()
    return file_path


def load_profile_txt(file_path: str) -> np.ndarray:
    """
    Lee un archivo TXT con dos columnas numéricas: x y
    Ignora encabezados, líneas vacías y texto no numérico.
    """
    points = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            parts = line.replace(",", " ").split()
            if len(parts) < 2:
                continue

            try:
                x = float(parts[0])
                y = float(parts[1])
                points.append([x, y])
            except ValueError:
                continue

    if len(points) < 4:
        raise ValueError("No se pudieron leer suficientes puntos válidos del archivo.")

    return np.array(points, dtype=float)


def trailing_edge_midpoint(points: np.ndarray) -> np.ndarray:
    """
    Define la cola (borde de salida) como el punto medio
    entre el primer y el último punto del archivo.
    """
    return 0.5 * (points[0] + points[-1])


def translate_te_to_origin(points: np.ndarray) -> np.ndarray:
    """
    Traslada todos los puntos para que la cola quede en el origen.
    """
    te = trailing_edge_midpoint(points)
    shifted = points.copy()
    shifted[:, 0] -= te[0]
    shifted[:, 1] -= te[1]
    return shifted


def chord_length(points: np.ndarray) -> float:
    """
    Calcula la cuerda como la distancia entre el borde de ataque
    y la cola definida en el borde de salida.
    """
    te = trailing_edge_midpoint(points)
    le = points[np.argmin(points[:, 0])]
    return np.linalg.norm(le - te)


def split_upper_lower(points: np.ndarray):
    """
    Divide el contorno en extradós e intradós usando el punto
    de x mínima como borde de ataque.
    """
    i_le = np.argmin(points[:, 0])

    upper = points[: i_le + 1].copy()
    lower = points[i_le:].copy()

    return upper, lower


def arc_length(polyline: np.ndarray) -> float:
    """
    Calcula la longitud de arco de una polilínea.
    """
    diffs = np.diff(polyline, axis=0)
    seg_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))
    return np.sum(seg_lengths)


def upper_surface_arc_length(points: np.ndarray) -> float:
    """
    Calcula la longitud del borde superior (extradós).
    """
    upper, _ = split_upper_lower(points)
    return arc_length(upper)


def resample_polyline(polyline: np.ndarray, n_points: int) -> np.ndarray:
    """
    Remuestrea una polilínea a n_points equiespaciados
    en longitud de arco.
    """
    if n_points < 2:
        raise ValueError("n_points debe ser al menos 2.")

    diffs = np.diff(polyline, axis=0)
    seg_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))
    s = np.concatenate(([0.0], np.cumsum(seg_lengths)))

    total_length = s[-1]
    if total_length == 0:
        raise ValueError("La polilínea tiene longitud cero.")

    s_new = np.linspace(0.0, total_length, n_points)
    x_new = np.interp(s_new, s, polyline[:, 0])
    y_new = np.interp(s_new, s, polyline[:, 1])

    return np.column_stack((x_new, y_new))


def scale_profile(points: np.ndarray, scale_factor: float) -> np.ndarray:
    """
    Escala el perfil completo.
    """
    return points * scale_factor


def max_thickness(points: np.ndarray, n_samples: int = 2000):
    """
    Calcula el grosor máximo del perfil como:
    thickness = y_upper - y_lower

    Retorna:
    - grosor máximo
    - posición x donde ocurre
    - y_upper en ese punto
    - y_lower en ese punto
    """
    upper, lower = split_upper_lower(points)

    upper_sorted = upper[np.argsort(upper[:, 0])]
    lower_sorted = lower[np.argsort(lower[:, 0])]

    x_upper = upper_sorted[:, 0]
    y_upper = upper_sorted[:, 1]

    x_lower = lower_sorted[:, 0]
    y_lower = lower_sorted[:, 1]

    x_min = max(np.min(x_upper), np.min(x_lower))
    x_max = min(np.max(x_upper), np.max(x_lower))

    if x_max <= x_min:
        raise ValueError("No hay rango común en x entre extradós e intradós.")

    x_common = np.linspace(x_min, x_max, n_samples)
    yu = np.interp(x_common, x_upper, y_upper)
    yl = np.interp(x_common, x_lower, y_lower)

    thickness = yu - yl
    i_max = np.argmax(thickness)

    return thickness[i_max], x_common[i_max], yu[i_max], yl[i_max]


def export_xyz(points_xy: np.ndarray, output_file: str):
    """
    Exporta archivo con columnas x, y, z.
    La columna z se llena con ceros.
    """
    z = np.zeros((points_xy.shape[0], 1))
    data = np.hstack((points_xy, z))

    np.savetxt(
        output_file,
        data,
        fmt="%.6f",
        delimiter=" ",
    )


def format_length_for_filename(value_mm: float) -> str:
    """
    Convierte una longitud a texto seguro para nombre de archivo.
    Ejemplo:
    120     -> 120
    120.5   -> 120_5
    120.25  -> 120_25
    """
    text = f"{value_mm:.2f}"
    text = text.rstrip("0").rstrip(".")
    text = text.replace(".", "_")
    return text


def plot_profiles(base_points: np.ndarray, second_points: np.ndarray):
    """
    Muestra una gráfica con ambos perfiles sobrepuestos.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(base_points[:, 0], base_points[:, 1], label="Perfil base")
    plt.plot(second_points[:, 0], second_points[:, 1], label="Perfil escalado por borde superior")
    plt.scatter([0], [0], marker="x", s=80, label="Cola en origen")

    plt.xlabel("x [mm]")
    plt.ylabel("y [mm]")
    plt.title("Perfiles sobrepuestos")
    plt.axis("equal")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def process_profile(
    input_file: str,
    base_chord_mm: float,
    upper_length_mm: float,
    n_output_points: int = 100
):
    """
    Procesa el perfil y genera:
    - archivo base escalado por cuerda
    - archivo escalado por longitud de borde superior
    - reporte
    - gráfica comparativa
    """
    raw_points = load_profile_txt(input_file)

    # ==========================================
    # PERFIL 1: ESCALADO POR CUERDA
    # ==========================================
    original_chord = chord_length(raw_points)
    if original_chord <= 0:
        raise ValueError("La cuerda original es inválida.")

    scale_base = base_chord_mm / original_chord
    base_scaled = scale_profile(raw_points, scale_base)
    base_shifted = translate_te_to_origin(base_scaled)
    base_resampled = resample_polyline(base_shifted, n_output_points)

    tmax_base, xtmax_base, yu_base, yl_base = max_thickness(base_shifted)

    # ==========================================
    # PERFIL 2: ESCALADO POR LONGITUD DE EXTRADÓS
    # ==========================================
    original_upper_len = upper_surface_arc_length(raw_points)
    if original_upper_len <= 0:
        raise ValueError("La longitud original del borde superior es inválida.")

    scale_upper = upper_length_mm / original_upper_len
    upper_scaled = scale_profile(raw_points, scale_upper)
    upper_shifted = translate_te_to_origin(upper_scaled)
    upper_resampled = resample_polyline(upper_shifted, n_output_points)

    tmax_upper, xtmax_upper, yu_upper, yl_upper = max_thickness(upper_shifted)

    input_path = Path(input_file)
    stem = input_path.stem
    out_dir = input_path.parent

    chord_name = format_length_for_filename(base_chord_mm)
    upper_name = format_length_for_filename(upper_length_mm)

    # ============================================================
    # NOTA: AQUÍ SE DEFINE EL NOMBRE DE LOS ARCHIVOS DE SALIDA
    # Si quieres cambiar cómo se llaman, modifica SOLO estas líneas
    # ============================================================
    base_file = out_dir / f"{stem}_chord_{chord_name}mm.txt"
    upper_file = out_dir / f"{stem}_upper_{upper_name}mm.txt"
    report_file = out_dir / f"{stem}_report_chord_{chord_name}mm_upper_{upper_name}mm.txt"

    export_xyz(base_resampled, str(base_file))
    export_xyz(upper_resampled, str(upper_file))

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("REPORTE DEL PERFIL\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Archivo de entrada: {input_file}\n")
        f.write(f"Puntos originales leídos: {len(raw_points)}\n")
        f.write(f"Puntos exportados por archivo: {n_output_points}\n\n")

        f.write("PERFIL 1: ESCALADO POR CUERDA\n")
        f.write("-" * 60 + "\n")
        f.write(f"Cuerda objetivo [mm]: {base_chord_mm:.6f}\n")
        f.write(f"Cuerda original [u archivo]: {original_chord:.6f}\n")
        f.write(f"Factor de escala: {scale_base:.8f}\n")
        f.write(f"Grosor máximo [mm]: {tmax_base:.6f}\n")
        f.write(f"Ubicación x de grosor máximo [mm]: {xtmax_base:.6f}\n")
        f.write(f"y_upper en tmax [mm]: {yu_base:.6f}\n")
        f.write(f"y_lower en tmax [mm]: {yl_base:.6f}\n")
        f.write(f"Archivo generado: {base_file.name}\n\n")

        f.write("PERFIL 2: ESCALADO POR LONGITUD DEL BORDE SUPERIOR\n")
        f.write("-" * 60 + "\n")
        f.write(f"Longitud objetivo borde superior [mm]: {upper_length_mm:.6f}\n")
        f.write(f"Longitud original borde superior [u archivo]: {original_upper_len:.6f}\n")
        f.write(f"Factor de escala: {scale_upper:.8f}\n")
        f.write(f"Grosor máximo [mm]: {tmax_upper:.6f}\n")
        f.write(f"Ubicación x de grosor máximo [mm]: {xtmax_upper:.6f}\n")
        f.write(f"y_upper en tmax [mm]: {yu_upper:.6f}\n")
        f.write(f"y_lower en tmax [mm]: {yl_upper:.6f}\n")
        f.write(f"Archivo generado: {upper_file.name}\n")

    return {
        "base_file": str(base_file),
        "upper_file": str(upper_file),
        "report_file": str(report_file),
        "base_resampled": base_resampled,
        "upper_resampled": upper_resampled,
        "tmax_base_mm": tmax_base,
        "tmax_upper_mm": tmax_upper,
        "xtmax_base_mm": xtmax_base,
        "xtmax_upper_mm": xtmax_upper,
    }


def main():
    print("=" * 60)
    print("GENERADOR DE PERFIL PARA SOLIDWORKS")
    print("=" * 60)
    print("\nSelecciona el archivo TXT del perfil.\n")

    input_file = select_file()

    if not input_file:
        print("No se seleccionó archivo.")
        return

    base_chord_mm = float(input("Cuerda objetivo del perfil base [mm]: ").strip())
    upper_length_mm = float(input("Longitud objetivo del borde superior [mm]: ").strip())

    npts_str = input("Número de puntos de salida [Enter = 100]: ").strip()
    n_output_points = int(npts_str) if npts_str else 100

    results = process_profile(
        input_file=input_file,
        base_chord_mm=base_chord_mm,
        upper_length_mm=upper_length_mm,
        n_output_points=n_output_points,
    )

    print("\nProceso terminado.\n")
    print(f"Archivo base generado:    {results['base_file']}")
    print(f"Archivo segundo generado: {results['upper_file']}")
    print(f"Reporte generado:         {results['report_file']}")
    print(f"Grosor máximo perfil base [mm]: {results['tmax_base_mm']:.6f}")
    print(f"Ubicación x tmax base [mm]:     {results['xtmax_base_mm']:.6f}")
    print(f"Grosor máximo perfil 2 [mm]:    {results['tmax_upper_mm']:.6f}")
    print(f"Ubicación x tmax perfil 2 [mm]: {results['xtmax_upper_mm']:.6f}")

    plot_profiles(results["base_resampled"], results["upper_resampled"])


if __name__ == "__main__":
    main()