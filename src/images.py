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
from safe_print import safe_print

load_dotenv()

class SocialMediaImageGenerator:
    def __init__(self):
        self.client = OpenAI()
        # Default size - portrait performs best on Instagram/Facebook feeds
        self.default_size = "1024x1536"  # 2:3 portrait format - best engagement
        self.output_dir = path_manager.get_path('imagenes')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load línea gráfica images as references
        self.style_images = self._load_style_images()
        # Also analyze for color palette (fallback for text description)
        self.style_guide = self._analyze_style_guide()

    def _load_style_images(self):
        """Load línea gráfica images as reference files for the edit endpoint."""
        style_images = []
        style_dir = path_manager.get_path('linea_grafica')

        if not style_dir.exists():
            safe_print("⚠️ Carpeta linea_grafica no encontrada")
            return style_images

        try:
            image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
            image_files = []
            for pattern in image_patterns:
                image_files.extend(style_dir.glob(pattern))

            if not image_files:
                safe_print("⚠️ No se encontraron imágenes en la carpeta linea_grafica")
                return style_images

            # Limit to 5 reference images (API supports up to 16, but we want efficiency)
            for img_path in sorted(image_files)[:5]:
                # Verify the image is valid and under 50MB
                if img_path.stat().st_size < 50 * 1024 * 1024:
                    style_images.append(str(img_path))
                    safe_print(f"✓ Imagen de referencia cargada: {img_path.name}")
                else:
                    safe_print(f"⚠️ Imagen muy grande (>50MB), omitida: {img_path.name}")

            safe_print(f"✓ {len(style_images)} imágenes de línea gráfica listas como referencia")

        except Exception as e:
            safe_print(f"✗ Error cargando imágenes de referencia: {str(e)}")

        return style_images

    def _analyze_style_guide(self):
        """Analiza las imágenes en la carpeta linea_grafica para extraer información de estilo"""
        style_info = {
            'colors': [],
            'compositions': []
        }

        style_dir = path_manager.get_path('linea_grafica')
        if not style_dir.exists():
            return style_info

        try:
            # Corregir el patrón de búsqueda para imágenes
            image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
            image_files = []
            for pattern in image_patterns:
                image_files.extend(style_dir.glob(pattern))

            if not image_files:
                return style_info

            for img_path in image_files:
                img = Image.open(img_path)

                # Extraer colores dominantes
                colors = self._get_dominant_colors(img)
                style_info['colors'].extend(colors)

                # Analizar composición
                composition = self._analyze_composition(img)
                style_info['compositions'].append(composition)

        except Exception as e:
            safe_print(f"✗ Error analizando línea gráfica: {str(e)}")

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

    def generate_image(self, prompt: str, platform: str, post_date: str, title: str, size: str = None) -> str:
        """Genera una imagen usando GPT-Image-1 con imágenes de referencia de línea gráfica.

        Args:
            prompt: Image description/prompt
            platform: Target platform (for logging)
            post_date: Date in YYYY-MM-DD format
            title: Post title (used for filename)
            size: Optional size - "1024x1536" (portrait), "1024x1024" (square),
                  "1536x1024" (landscape), or "auto". Defaults to portrait.
        """
        try:
            # Validate and set size
            valid_sizes = ["1024x1024", "1024x1536", "1536x1024", "auto"]
            if size is None or size not in valid_sizes:
                size = self.default_size

            size_names = {
                "1024x1536": "portrait",
                "1024x1024": "square",
                "1536x1024": "landscape",
                "auto": "auto"
            }
            safe_print(f"📐 Generando imagen en formato {size_names.get(size, size)} ({size})")

            # Build enhanced prompt with style instructions
            style_prompt = self._create_style_prompt()
            enhanced_prompt = f"""{prompt}

IMPORTANT: Match the visual style, color palette, and aesthetic of the reference images provided.
{style_prompt}
"""

            # Use edit endpoint with reference images if available
            if self.style_images:
                safe_print(f"🎨 Usando {len(self.style_images)} imágenes de referencia de línea gráfica")

                # Open reference images as file objects
                image_files = [open(img_path, "rb") for img_path in self.style_images]

                try:
                    response = self.client.images.edit(
                        model="gpt-image-1",
                        image=image_files,
                        prompt=enhanced_prompt,
                        size=size,
                        quality="high",
                        input_fidelity="high",  # Match style closely
                        n=1
                    )
                finally:
                    # Close all file handles
                    for f in image_files:
                        f.close()
            else:
                # Fallback to generate endpoint if no reference images
                safe_print("⚠️ Sin imágenes de referencia, usando generación estándar")
                response = self.client.images.generate(
                    model="gpt-image-1",
                    prompt=enhanced_prompt,
                    size=size,
                    quality="high",
                    n=1
                )

            image_b64 = response.data[0].b64_json

            if not image_b64:
                safe_print(f"✗ Error: No se recibió data de la imagen para {platform}.")
                return ""

            # Decode and save image
            image_bytes = base64.b64decode(image_b64)
            img = Image.open(BytesIO(image_bytes))

            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{post_date}_{safe_title[:50]}.png"
            filepath = self.output_dir / filename

            img.save(filepath)
            safe_print(f"✓ Imagen guardada: {filename}")

            return str(filepath)

        except Exception as e:
            safe_print(f"✗ Error generando imagen para {platform}: {str(e)}")
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

            safe_print(f"\nProcesando calendario: {csv_path}")
            safe_print("="*50)

            # Column for universal image that works on all platforms
            df['universal_image'] = ''

            # Procesar cada fila
            for idx, row in df.iterrows():
                safe_print(f"\nPublicación {idx+1}: {row['titulo']}")

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
                safe_print("Generando imagen universal para todas las plataformas...")
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
            safe_print(f"\n✓ CSV actualizado guardado en: {output_csv}")

        except Exception as e:
            safe_print(f"\n✗ Error procesando {csv_path}: {str(e)}")

# ============================================================================
# Standalone Functions for Tool Use
# ============================================================================

def generate_single_image(
    titulo: str,
    imagen_description: str,
    fecha: str,
    style_colors: list = None,
    size: str = "1024x1536"
) -> str:
    """
    Generate a single image using GPT-Image-1 with línea gráfica as reference.

    This is a standalone function that can be used by tools or other modules
    without instantiating the full SocialMediaImageGenerator class.

    Args:
        titulo: The post title (used for filename and context)
        imagen_description: Detailed description for the image
        fecha: The post date in YYYY-MM-DD format (used for filename)
        style_colors: Optional list of hex colors for brand consistency
        size: Image dimensions - "1024x1536" (portrait), "1024x1024" (square),
              "1536x1024" (landscape), or "auto"

    Returns:
        Path to the saved image file, or empty string on error
    """
    try:
        client = OpenAI()
        output_dir = path_manager.get_path('imagenes')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load línea gráfica images as references
        style_images = []
        style_dir = path_manager.get_path('linea_grafica')

        if style_dir.exists():
            try:
                image_files = []
                for pattern in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                    image_files.extend(style_dir.glob(pattern))

                # Limit to 5 reference images
                for img_path in sorted(image_files)[:5]:
                    if img_path.stat().st_size < 50 * 1024 * 1024:  # Under 50MB
                        style_images.append(str(img_path))

                if style_images:
                    safe_print(f"🎨 Usando {len(style_images)} imágenes de línea gráfica como referencia")
            except Exception as e:
                safe_print(f"⚠️ Error cargando imágenes de referencia: {e}")

        # Build style prompt for additional context
        style_prompt = ""
        if style_colors:
            colors_str = ", ".join(style_colors[:5])
            style_prompt = f"\nUse this specific color palette: {colors_str}"
        elif style_images:
            # Extract colors from first reference image
            try:
                img = Image.open(style_images[0])
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail((150, 150))
                pixels = list(img.getdata())
                color_counts = {}
                for pixel in pixels:
                    if pixel in color_counts:
                        color_counts[pixel] += 1
                    else:
                        color_counts[pixel] = 1
                dominant = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                colors = ['#{:02x}{:02x}{:02x}'.format(c[0][0], c[0][1], c[0][2]) for c in dominant]
                colors_str = ", ".join(colors)
                style_prompt = f"\nUse this brand color palette: {colors_str}"
            except Exception:
                pass

        # Build enhanced prompt
        enhanced_prompt = f"""Create a social media image for the following post:

Title: {titulo}
Image description: {imagen_description}

IMPORTANT: Match the visual style, color palette, and aesthetic of the reference images provided.

Additional requirements:
- Professional and attractive visual style
- Vibrant but not oversaturated colors
- Balanced composition
- If text is requested, render it clearly and legibly
- High quality and detail
- Style coherent with the CAUSA brand (if including logo, only the butterfly and 'CAUSA' below it)
{style_prompt}
"""

        # Validate and set size
        valid_sizes = ["1024x1024", "1024x1536", "1536x1024", "auto"]
        if size not in valid_sizes:
            size = "1024x1536"  # Default to portrait

        size_names = {
            "1024x1536": "portrait",
            "1024x1024": "square",
            "1536x1024": "landscape",
            "auto": "auto"
        }
        safe_print(f"📐 Generando imagen en formato {size_names.get(size, size)} ({size})")

        # Use edit endpoint with reference images if available
        if style_images:
            image_files = [open(img_path, "rb") for img_path in style_images]

            try:
                response = client.images.edit(
                    model="gpt-image-1",
                    image=image_files,
                    prompt=enhanced_prompt,
                    size=size,
                    quality="high",
                    input_fidelity="high",  # Match style closely
                    n=1
                )
            finally:
                for f in image_files:
                    f.close()
        else:
            # Fallback to generate endpoint if no reference images
            safe_print("⚠️ Sin imágenes de referencia, usando generación estándar")
            response = client.images.generate(
                model="gpt-image-1",
                prompt=enhanced_prompt,
                size=size,
                quality="high",
                n=1
            )

        image_b64 = response.data[0].b64_json

        if not image_b64:
            safe_print("Error: No image data received")
            return ""

        # Decode and save image
        image_bytes = base64.b64decode(image_b64)
        img = Image.open(BytesIO(image_bytes))

        # Create safe filename
        safe_title = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{fecha}_{safe_title[:50]}.png"
        filepath = output_dir / filename

        img.save(filepath)
        safe_print(f"✓ Imagen guardada: {filename}")

        return str(filepath)

    except Exception as e:
        safe_print(f"Error generating image: {str(e)}")
        return ""


def main():
    # Crear instancia del generador
    generator = SocialMediaImageGenerator()

    # Asegurarse que existe el directorio de publicaciones
    path_manager.ensure_directories()

    # Obtener todos los archivos CSV que coincidan con el patrón
    publicaciones_dir = path_manager.get_path('publicaciones')
    csv_files = list(publicaciones_dir.glob('social_media_calendar_*.csv'))

    if not csv_files:
        safe_print("No se encontraron archivos CSV para procesar")
        return

    safe_print(f"Encontrados {len(csv_files)} archivos CSV para procesar")

    # Crear una lista para almacenar todos los DataFrames
    all_dfs = []

    # Leer y combinar todos los archivos CSV
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
            safe_print(f"Leído archivo: {csv_file}")
        except Exception as e:
            safe_print(f"Error al leer {csv_file}: {str(e)}")

    if not all_dfs:
        safe_print("No se pudieron leer archivos CSV válidos")
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
    safe_print(f"\nArchivo combinado guardado en: {output_path}")

    # Procesar el archivo combinado
    try:
        generator.process_calendar(output_path)
        safe_print("\n✓ Procesamiento completado exitosamente")
    except Exception as e:
        safe_print(f"\n✗ Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    main()
