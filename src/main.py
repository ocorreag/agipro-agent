import pandas as pd
import agent
import images
from csv_manager import PostManager
from path_manager import setup_environment

def cleanup_old_posts(pm: PostManager):
    """
    Limpia publicaciones mayores a 4 meses
    """
    print("\n=== Limpieza de publicaciones antiguas ===")

    try:
        pm.cleanup_old_files()
    except Exception as e:
        print(f"✗ Error en limpieza: {str(e)}")

def process_images_for_posts(pm: PostManager, csv_file: str):
    """
    Procesa las imágenes para los posts y actualiza los archivos CSV con las rutas
    """
    print("\n=== Generando imágenes ===")
    try:
        image_generator = images.SocialMediaImageGenerator()
        image_generator.process_calendar(csv_file)

        # Leer el CSV actualizado con las rutas de imágenes
        df_with_images = pd.read_csv(csv_file)

        # Actualizar los archivos de borradores con las rutas de las imágenes
        for _, row in df_with_images.iterrows():
            fecha = row['fecha']
            titulo = row['titulo']

            # Buscar la ruta de imagen generada
            image_path = None
            # Check for universal image first, then fallback to old column names
            if 'universal_image' in df_with_images.columns and pd.notna(row['universal_image']):
                image_path = row['universal_image']
            else:
                # Fallback to old column names for backward compatibility
                for col in ['instagram_image', 'facebook_image']:
                    if col in df_with_images.columns and pd.notna(row[col]):
                        image_path = row[col]
                        break

            if image_path:
                pm.update_image_path(fecha, titulo, image_path)

        print("✓ Imágenes generadas y rutas actualizadas en los archivos CSV")

    except Exception as e:
        print(f"✗ Error generando imágenes: {str(e)}")


def display_summary(pm: PostManager):
    """
    Muestra un resumen de las publicaciones generadas
    """
    print("\n=== Resumen de Publicaciones Generadas ===")

    try:
        draft_posts = pm.get_draft_posts()
        stats = pm.get_stats()

        if draft_posts:
            print(f"✓ Se generaron {len(draft_posts)} nuevas publicaciones:")
            for post in draft_posts:
                print(f"  - {post['fecha']}: {post['titulo']}")

            print(f"\n📊 Estadísticas:")
            print(f"  - Total borradores: {stats['total_drafts']}")
            print(f"  - Total publicadas: {stats['total_published']}")
            print(f"  - Posts por día configurado: {stats['settings']['posts_per_day']}")

            print("\n💡 Usa el frontend de Streamlit para revisar y editar las publicaciones antes de publicar.")
        else:
            print("⚠️ No se generaron publicaciones nuevas")

    except Exception as e:
        print(f"✗ Error al mostrar resumen: {str(e)}")


def main():
    try:
        print("\n=== Iniciando proceso de generación de contenido ===")

        # Setup environment and paths
        setup_environment()

        # Inicializar gestor de CSV
        pm = PostManager()

        # Limpiar publicaciones antiguas
        cleanup_old_posts(pm)

        # Obtener configuración de posts por día
        posts_per_day = int(pm.get_setting('posts_per_day', 3))
        print(f"\n=== Configuración: {posts_per_day} posts por día ===")

        # Generar nuevo contenido con Agent
        print("\n=== Generando nuevo contenido con Agent ===")
        agent.setup_directories()
        calendar = agent.generate_social_media_calendar(days=2, posts_per_day=posts_per_day)

        if calendar:
            # Guardar posts como borradores
            new_posts = []
            for post in calendar:
                new_posts.append({
                    'fecha': post['fecha'],
                    'titulo': post['titulo'],
                    'imagen': post['imagen'],
                    'descripcion': post['descripcion']
                })

            pm.save_draft_posts(new_posts)

            # Exportar a CSV para compatibilidad con generador de imágenes
            csv_file = pm.export_for_image_generation()
            if csv_file:
                print(f"✓ CSV temporal exportado: {csv_file}")

                # Procesar imágenes
                process_images_for_posts(pm, csv_file)

            # Mostrar resumen
            display_summary(pm)

        else:
            print("\n⚠️ No se generó contenido nuevo")

        print("\n✓ Proceso completado exitosamente")
        print("\n💡 Ejecuta 'streamlit run frontend.py' para revisar y publicar el contenido")

    except Exception as e:
        print(f"\n✗ Error en el proceso: {str(e)}")

if __name__ == "__main__":
    main()
