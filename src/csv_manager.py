import os
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from path_manager import path_manager

class PostManager:
    def __init__(self):
        # Use centralized path management
        self.base_dir = path_manager.get_path('publicaciones')
        self.drafts_dir = path_manager.get_path('drafts')
        self.published_file = path_manager.get_path('published_posts')
        self.settings_file = path_manager.get_path('settings')

        self.setup_directories()
        self.setup_settings()

    def setup_directories(self):
        """Create necessary directories"""
        # Use path manager to ensure directories
        path_manager.ensure_directories()

    def setup_settings(self):
        """Create settings file with defaults"""
        if not self.settings_file.exists():
            default_settings = {
                "posts_per_day": 3,
                "cleanup_months": 4
            }
            self.save_settings(default_settings)

    def save_settings(self, settings: Dict):
        """Save settings to JSON file"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def load_settings(self) -> Dict:
        """Load settings from JSON file"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"posts_per_day": 3, "cleanup_months": 4}

    def update_setting(self, key: str, value):
        """Update a specific setting"""
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)

    def get_setting(self, key: str, default=None):
        """Get a specific setting"""
        settings = self.load_settings()
        return settings.get(key, default)

    def save_draft_posts(self, posts: List[Dict], date: str = None) -> str:
        """Save new posts as drafts for a specific date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        draft_file = self.drafts_dir / f"posts_{date}.csv"

        # Add status and metadata columns
        for post in posts:
            post['status'] = 'draft'
            post['created_at'] = datetime.now().isoformat()
            post['image_path'] = ''

        df = pd.DataFrame(posts)

        # Ensure columns are in correct order
        columns = ['fecha', 'titulo', 'imagen', 'descripcion', 'status', 'created_at', 'image_path']
        df = df.reindex(columns=columns, fill_value='')

        # Ensure image_path column is string type from the start
        df['image_path'] = df['image_path'].astype('str')

        df.to_csv(draft_file, index=False, encoding='utf-8')
        print(f"✓ {len(posts)} posts guardados como borradores en: {draft_file}")

        return str(draft_file)

    def get_draft_posts(self, date: str = None) -> List[Dict]:
        """Get draft posts for a specific date or all drafts"""
        draft_files = []

        if date:
            draft_file = self.drafts_dir / f"posts_{date}.csv"
            if draft_file.exists():
                draft_files = [draft_file]
        else:
            draft_files = list(self.drafts_dir.glob("posts_*.csv"))

        all_drafts = []
        for file in sorted(draft_files):
            try:
                df = pd.read_csv(file, encoding='utf-8')
                # Fill NaN values to avoid TypeError when accessing fields
                df = df.fillna('')
                # Ensure image_path column is string type
                if 'image_path' in df.columns:
                    df['image_path'] = df['image_path'].astype('str')
                # Only return drafts, not published
                drafts = df[df['status'] == 'draft'].to_dict('records')

                # Add file info for easier management
                for draft in drafts:
                    draft['draft_file'] = str(file)

                all_drafts.extend(drafts)
            except Exception as e:
                print(f"Error leyendo {file}: {e}")

        return all_drafts

    def update_post_status(self, fecha: str, titulo: str, new_status: str):
        """Update post status in the draft file"""
        draft_file = self.drafts_dir / f"posts_{fecha}.csv"

        if not draft_file.exists():
            return False

        try:
            df = pd.read_csv(draft_file, encoding='utf-8')

            # Find the specific post
            mask = (df['fecha'] == fecha) & (df['titulo'] == titulo)
            if not mask.any():
                return False

            df.loc[mask, 'status'] = new_status
            df.loc[mask, 'updated_at'] = datetime.now().isoformat()

            df.to_csv(draft_file, index=False, encoding='utf-8')

            # If publishing, also add to published file
            if new_status == 'published':
                self._add_to_published(df.loc[mask].iloc[0])

            return True

        except Exception as e:
            print(f"Error actualizando post: {e}")
            return False

    def update_post_content(self, fecha: str, titulo_original: str, nuevo_titulo: str, nueva_descripcion: str, nueva_imagen: str = None):
        """Update post content in draft file"""
        draft_file = self.drafts_dir / f"posts_{fecha}.csv"

        if not draft_file.exists():
            return False

        try:
            df = pd.read_csv(draft_file, encoding='utf-8')

            # Find the specific post by original title
            mask = (df['fecha'] == fecha) & (df['titulo'] == titulo_original)
            if not mask.any():
                return False

            df.loc[mask, 'titulo'] = nuevo_titulo
            df.loc[mask, 'descripcion'] = nueva_descripcion
            if nueva_imagen:
                df.loc[mask, 'imagen'] = nueva_imagen
            df.loc[mask, 'updated_at'] = datetime.now().isoformat()

            df.to_csv(draft_file, index=False, encoding='utf-8')
            return True

        except Exception as e:
            print(f"Error actualizando contenido: {e}")
            return False

    def update_image_path(self, fecha: str, titulo: str, image_path: str):
        """Update the image path for a specific post"""
        # First try the exact date file
        draft_file = self.drafts_dir / f"posts_{fecha}.csv"

        # If exact date file doesn't exist, search all draft files
        if not draft_file.exists():
            draft_files = list(self.drafts_dir.glob("posts_*.csv"))
        else:
            draft_files = [draft_file]

        for file_path in draft_files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')

                mask = (df['fecha'] == fecha) & (df['titulo'] == titulo)
                if mask.any():
                    # Ensure image_path column is string type to avoid dtype warning
                    df['image_path'] = df['image_path'].astype('str')
                    df.loc[mask, 'image_path'] = image_path
                    df.to_csv(file_path, index=False, encoding='utf-8')
                    print(f"Updated image path for '{titulo}' in {file_path.name}")
                    return True

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        print(f"Post not found: {fecha} - {titulo}")
        return False

    def _add_to_published(self, post_data):
        """Add post to published posts file"""
        published_data = {
            'fecha': post_data['fecha'],
            'titulo': post_data['titulo'],
            'descripcion': post_data['descripcion'],
            'image_path': post_data.get('image_path', ''),
            'published_at': datetime.now().isoformat()
        }

        # Create or append to published file
        file_exists = self.published_file.exists()

        with open(self.published_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=published_data.keys())

            if not file_exists:
                writer.writeheader()

            writer.writerow(published_data)

    def get_published_posts(self) -> List[Dict]:
        """Get all published posts"""
        if not self.published_file.exists():
            return []

        try:
            df = pd.read_csv(self.published_file, encoding='utf-8')
            return df.to_dict('records')
        except:
            return []

    def cleanup_old_files(self, months_old: int = None):
        """Clean up old draft files and images"""
        if months_old is None:
            months_old = self.get_setting('cleanup_months', 4)

        cutoff_date = datetime.now() - timedelta(days=months_old * 30)

        cleaned_files = 0
        cleaned_images = 0

        # Clean draft files
        for draft_file in self.drafts_dir.glob("posts_*.csv"):
            try:
                # Extract date from filename
                date_str = draft_file.stem.replace('posts_', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    # Clean associated images first
                    try:
                        df = pd.read_csv(draft_file, encoding='utf-8')
                        for _, row in df.iterrows():
                            image_path = row.get('image_path', '')
                            if image_path and os.path.exists(image_path):
                                os.remove(image_path)
                                cleaned_images += 1
                    except:
                        pass

                    draft_file.unlink()
                    cleaned_files += 1

            except ValueError:
                # Skip files with invalid date format
                continue

        print(f"✓ Limpieza completada: {cleaned_files} archivos y {cleaned_images} imágenes eliminados")
        return cleaned_files, cleaned_images

    def export_for_image_generation(self, date: str = None) -> str:
        """Export draft posts to CSV format compatible with image generator"""
        drafts = self.get_draft_posts(date)

        if not drafts:
            return None

        # Convert to the format expected by image generator
        export_data = []
        for draft in drafts:
            export_data.append({
                'fecha': draft['fecha'],
                'titulo': draft['titulo'],
                'imagen': draft['imagen'],
                'descripcion': draft['descripcion']
            })

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = self.base_dir / f"temp_export_{timestamp}.csv"

        df = pd.DataFrame(export_data)
        df.to_csv(export_file, index=False, encoding='utf-8')

        return str(export_file)

    def get_stats(self) -> Dict:
        """Get statistics about posts"""
        drafts = self.get_draft_posts()
        published = self.get_published_posts()

        return {
            'total_drafts': len(drafts),
            'total_published': len(published),
            'draft_files': len(list(self.drafts_dir.glob("posts_*.csv"))),
            'settings': self.load_settings()
        }
