import base64
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
from dotenv import load_dotenv
import glob
from path_manager import path_manager

load_dotenv()

class SocialMediaImageGenerator:
    def __init__(self):
        self.client = OpenAI()
        # Universal size that works across all social media platforms
        self.universal_size = "1024x1024"  # 1:1 square format - most versatile and DALL-E 3 compatible
        self.output_dir = path_manager.get_path('imagenes')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Analizar imágenes de línea gráfica
        self.style_guide = self._analyze_style_guide()

    def _analyze_style_guide(self):
        """Analiza las imágenes en la carpeta linea_grafica para extraer información de estilo"""
        style_info = {
            'colors': [],
            'compositions': []
        }

        style_dir = path_manager.get_path('linea_grafica')
        if not style_dir.exists():
            print("⚠️ Carpeta linea_grafica no encontrada")
            return style_info

        try:
            # Corregir el patrón de búsqueda para imágenes
            image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
            image_files = []
            for pattern in image_patterns:
                image_files.extend(style_dir.glob(pattern))

            if not image_files:
                print("⚠️ No se encontraron imágenes en la carpeta linea_grafica")
                return style_info

            for img_path in image_files:
                print(f"Analizando imagen: {img_path.name}")
                img = Image.open(img_path)

                # Extraer colores dominantes
                colors = self._get_dominant_colors(img)
                style_info['colors'].extend(colors)

                # Analizar composición
                composition = self._analyze_composition(img)
                style_info['compositions'].append(composition)

            print(f"✓ Analizadas {len(style_info['compositions'])} imágenes de línea gráfica")
            print(f"Colores dominantes encontrados: {', '.join(style_info['colors'][:5])}")

        except Exception as e:
            print(f"✗ Error analizando línea gráfica: {str(e)}")

        return style_info

    def _get_dominant_colors(self, img):
        """Extrae los colores dominantes de una imagen"""
        # Convertir a RGB si es necesario
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Reducir tamaño para análisis más rápido
        img.thumbnail((150, 150))

        # Convertir a lista de pixels
        pixels = list(img.getdata())

        # Encontrar colores únicos más frecuentes
        color_counts = {}
        for pixel in pixels:
            if pixel in color_counts:
                color_counts[pixel] += 1
            else:
                color_counts[pixel] = 1

        # Obtener los 5 colores más frecuentes
        dominant = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [self._rgb_to_hex(color[0]) for color in dominant]

    def _rgb_to_hex(self, rgb):
        """Convierte tupla RGB a código hexadecimal"""
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def _analyze_composition(self, img):
        """Analiza la composición de la imagen"""
        width, height = img.size
        aspect_ratio = width/height

        return {
            'aspect_ratio': aspect_ratio,
            'orientation': 'horizontal' if width > height else 'vertical',
            'size': (width, height)
        }

    def generate_image(self, prompt: str, platform: str, post_date: str, title: str) -> str:
        """Genera una imagen usando DALL-E 3 con alta calidad y la guarda"""
        try:
            # Crear prompt con estilo visual
            style_prompt = self._create_style_prompt()
            enhanced_prompt = f"""{prompt}

            Aplica el siguiente estilo visual:
            {style_prompt}
            """

            # Generar imagen
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=enhanced_prompt,
                size=self.universal_size,
                quality="high",
                n=1
            )
            #print(response)
            image_b64 = response.data[0].b64_json

            if not image_b64:
                print(f"✗ Error: No se recibió data de la imagen para {platform}.")
                return ""

            # Decodificar y guardar imagen
            image_bytes = base64.b64decode(image_b64)
            img = Image.open(BytesIO(image_bytes))

            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{post_date}_{safe_title[:50]}.png"  # No platform prefix since it's universal
            filepath = self.output_dir / filename

            img.save(filepath)
            print(f"✓ Imagen guardada: {filename}")

            return str(filepath)

        except Exception as e:
            print(f"✗ Error generando imagen para {platform}: {str(e)}")
            return ""

    def _create_style_prompt(self):
        """Crea un prompt describiendo el estilo visual basado en el análisis de la línea gráfica"""
        if not self.style_guide['colors']:
            return ""

        colors_str = ", ".join(self.style_guide['colors'][:5])

        return f"""
        Usa esta paleta de colores específica: {colors_str}

        Características de estilo:
        - Mantén consistencia con la línea gráfica existente
        - Usa los colores corporativos mencionados como dominantes
        - Aplica un estilo limpio y minimalista
        - Mantén espacios negativos balanceados
        - Usa formas geométricas simples cuando sea apropiado
        - Evita elementos decorativos excesivos
        """

    def process_calendar(self, csv_path: str) -> None:
        """Procesa un archivo CSV y genera imágenes para cada publicación"""
        try:
            # Leer CSV
            df = pd.read_csv(csv_path)

            print(f"\nProcesando calendario: {csv_path}")
            print("="*50)

            # Column for universal image that works on all platforms
            df['universal_image'] = ''

            # Procesar cada fila
            for idx, row in df.iterrows():
                print(f"\nPublicación {idx+1}: {row['titulo']}")

                # Generar prompt mejorado
                base_prompt = f"""Crea una imagen para una publicación en redes sociales con el siguiente contenido:
                Título: {row['titulo']}
                Descripción de la imagen: {row['imagen']}

                Requisitos adicionales:
                - Estilo visual profesional y atractivo
                - Colores vibrantes pero no saturados
                - Composición balanceada
                - Si la descripción de la imagen pide texto, renderízalo de forma clara y legible.
                - Alta calidad y detalle
                - Estilo coherente con la marca CAUSA (sí vas a incluir el logo, solo la mariposa y el 'CAUSA)' debajo de la mariposa, pero no el texto completo de la marca que está en la parte de arriba de la imagen)
                """

                # Generate single universal image for all platforms
                print("Generando imagen universal para todas las plataformas...")
                image_path = self.generate_image(
                    base_prompt,
                    'universal',  # Single platform identifier
                    row['fecha'],
                    row['titulo']
                )
                df.at[idx, 'universal_image'] = image_path
                time.sleep(1)  # Reduced wait time since generating only one image

            # Guardar CSV actualizado en la carpeta de publicaciones
            output_csv = path_manager.get_path('publicaciones') / Path(csv_path).name
            df.to_csv(output_csv, index=False)
            print(f"\n✓ CSV actualizado guardado en: {output_csv}")

        except Exception as e:
            print(f"\n✗ Error procesando {csv_path}: {str(e)}")

def main():
    # Crear instancia del generador
    generator = SocialMediaImageGenerator()

    # Asegurarse que existe el directorio de publicaciones
    path_manager.ensure_directories()

    # Obtener todos los archivos CSV que coincidan con el patrón
    publicaciones_dir = path_manager.get_path('publicaciones')
    csv_files = list(publicaciones_dir.glob('social_media_calendar_*.csv'))

    if not csv_files:
        print("No se encontraron archivos CSV para procesar")
        return

    print(f"Encontrados {len(csv_files)} archivos CSV para procesar")

    # Crear una lista para almacenar todos los DataFrames
    all_dfs = []

    # Leer y combinar todos los archivos CSV
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
            print(f"Leído archivo: {csv_file}")
        except Exception as e:
            print(f"Error al leer {csv_file}: {str(e)}")

    if not all_dfs:
        print("No se pudieron leer archivos CSV válidos")
        return

    # Concatenar todos los DataFrames en uno solo
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Eliminar duplicados si los hay
    combined_df = combined_df.drop_duplicates()

    # Ordenar por fecha
    if 'fecha' in combined_df.columns:
        combined_df['fecha'] = pd.to_datetime(combined_df['fecha'])
        combined_df = combined_df.sort_values('fecha')

    # Guardar el archivo combinado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = path_manager.get_path('publicaciones') / f'social_media_calendar_combined_{timestamp}.csv'
    combined_df.to_csv(output_path, index=False)
    print(f"\nArchivo combinado guardado en: {output_path}")

    # Procesar el archivo combinado
    try:
        generator.process_calendar(output_path)
        print("\n✓ Procesamiento completado exitosamente")
    except Exception as e:
        print(f"\n✗ Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    main()
