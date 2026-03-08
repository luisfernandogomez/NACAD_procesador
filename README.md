# NACAD_procesador
Procesador de perfiles aerodinámicos para CAD

El programa:
Lee archivos .txt con coordenadas x y
Escala el perfil según:
cuerda deseada
longitud del borde superior
Alinea la cola del perfil en el origen
Genera 100 puntos remuestreados
Exporta archivos compatibles con SolidWorks y posiblemente otros CAD (x y z)
Calcula el grosor máximo del perfil
Muestra una gráfica comparativa de los perfiles generados

Ejemplo de entrada
Archivo .txt con dos columnas:
x y
1.000000 0.001050
0.950000 0.012340
0.900000 0.023120
...
Archivos generados

El programa genera:

perfil_chord_120mm.txt
perfil_upper_85mm.txt
perfil_report.txt

Los archivos contienen:

x y z

sin encabezados, compatibles con la importación de curvas en SolidWorks.

Instalación

Requiere Python 3 y las siguientes librerías:

numpy
matplotlib

Uso
Ejecutar el script:
python procesador_perfiles.py

Luego:
Seleccionar el archivo .txt del perfil
Introducir la cuerda deseada (mm)
Introducir la longitud del borde superior (mm)

El programa generará automáticamente los archivos de salida.

Visualización

Al finalizar se muestra una gráfica con ambos perfiles sobrepuestos para verificar la geometría.
Aplicaciones

Este script es útil para:
preparación rápida de perfiles para CAD
generación de perfiles para modelado en SolidWorks
análisis geométrico básico de perfiles aerodinámicos
preparación de perfiles para prototipado o fabricación

Licencia
Uso libre para fines académicos o de ingeniería.
