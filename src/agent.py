import os
from datetime import datetime, timedelta
from typing import Annotated, List, TypedDict
from pathlib import Path
import pandas as pd
from langchain_openai import ChatOpenAI
from urllib.parse import quote

from duckduckgo_search import DDGS
from langchain_core.messages import SystemMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
import json
from json_parser import parse_posts_from_llm_response
from config_manager import ConfigManager
from path_manager import path_manager
from safe_print import safe_print

load_dotenv()

# Initialize configuration manager
config_manager = ConfigManager()

def setup_directories():
    """Crea la estructura de directorios necesaria"""
    # Use centralized path management
    path_manager.ensure_directories()

class ContentPost(TypedDict):
    fecha: str
    titulo: str
    imagen: str
    descripcion: str

class State(TypedDict):
    messages: Annotated[List, add_messages]
    posts: List[ContentPost]
    memory_docs: str
    current_date: str

def get_news_for_date(date: str) -> str:
    """Busca noticias para una fecha específica en la web relacionadas con los temas del colectivo."""
    try:
        # Temas relevantes para el colectivo (configurables)
        temas_colectivo = config_manager.get_setting('collective_topics',
            "medio ambiente, animalismo, derechos humanos, urbanismo, política, cultura, Usaquén, Bogotá, Colombia")

        # Parse date to include in the query
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        today = datetime.now()

        # If the date is in the future, we look for the most recent news available (today's news).
        # The LLM will then use these recent news to create content for the future date.
        # If the date is today or in the past, we can search for news of that specific day.
        # This will prevent getting old news, by being more specific with the date.

        search_date = date_obj
        if date_obj.date() > today.date():
            search_date = today

        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        month_name = meses[search_date.month - 1]

        query = f"noticias del {search_date.day} de {month_name} de {search_date.year} en Colombia sobre {temas_colectivo}"

        safe_print(f"Buscando noticias con la consulta: {query}")

        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=7, region="co-es", safesearch="moderate"))

        if not results:
            # Fallback search without specific date
            fallback_query = f"Colombia {temas_colectivo} noticias recientes"
            safe_print(f"Sin resultados específicos, probando consulta alternativa: {fallback_query}")
            with DDGS() as ddgs:
                results = list(ddgs.news(fallback_query, max_results=5, region="co-es"))

        if not results:
            return f"No se encontraron noticias para la fecha consultada ({search_date.strftime('%Y-%m-%d')})."

        formatted_results = f"Noticias encontradas para la fecha {search_date.strftime('%Y-%m-%d')}:\n"
        for r in results:
            # DuckDuckGo news format: {'title', 'body', 'url', 'date', 'source'}
            formatted_results += f"- {r.get('title', '')}: {r.get('body', '')} (Fuente: {r.get('source', 'N/A')})\n"

        return formatted_results
    except Exception as e:
        safe_print(f"Error buscando noticias: {str(e)}")
        return "Error al buscar noticias."

def get_ephemerides(date: str) -> str:
    """Busca efemérides para una fecha específica en la web relacionadas con los temas del colectivo."""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        month_name = meses[date_obj.month - 1]

        # Temas relevantes para el colectivo
        temas_colectivo = "historia de Colombia, derechos humanos, memoria, animalismo, medio ambiente, educación popular, cultura"

        query = f"efemérides del {date_obj.day} de {month_name} en Colombia relacionadas con {temas_colectivo}"

        safe_print(f"Buscando efemérides con la consulta: {query}")

        with DDGS() as ddgs:
            # Use text search for ephemerides as they're more historical
            results = list(ddgs.text(query, max_results=7, region="co-es", safesearch="moderate"))

        if not results:
            # Fallback search with more general terms
            fallback_query = f"{date_obj.day} {month_name} efemérides Colombia historia"
            safe_print(f"Sin resultados específicos, probando consulta alternativa: {fallback_query}")
            with DDGS() as ddgs:
                results = list(ddgs.text(fallback_query, max_results=5, region="co-es"))

        if not results:
            return "No se encontraron efemérides para hoy."

        formatted_results = "Efemérides encontradas para hoy:\n"
        for r in results:
            # DuckDuckGo text format: {'title', 'body', 'href'}
            formatted_results += f"- {r.get('title', '')}: {r.get('body', '')}\n"

        return formatted_results
    except Exception as e:
        safe_print(f"Error buscando efemérides: {str(e)}")
        return "Error al buscar efemérides."

def get_activities_from_sheet():
    """Lee las actividades desde una Google Sheet pública y las filtra."""
    try:
        # Get configurable Google Sheets settings
        gsheet_id = config_manager.get_setting('google_sheet_id', '1dL7ngg0P-E9QEiWCDtS5iF2ColQC7YVIM4pbIPQouuE')
        sheet_name = config_manager.get_setting('google_sheet_name', 'actividades')
        # URL encode the sheet name to handle spaces and special characters
        encoded_sheet_name = quote(sheet_name)
        url = f'https://docs.google.com/spreadsheets/d/{gsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}'

        safe_print(f"Leyendo actividades desde Google Sheet: {url}")
        all_activities = pd.read_csv(url)

        if 'status' in all_activities.columns:
            confirmed_activities = all_activities[all_activities['status'].str.lower() == 'confirmada'].copy()
            safe_print(f"Se encontraron {len(confirmed_activities)} actividades confirmadas.")
            return confirmed_activities
        else:
            safe_print("La columna 'status' no se encontró. Devolviendo todas las actividades.")
            return all_activities

    except Exception as e:
        safe_print(f"Error al leer actividades desde Google Sheets: {str(e)}")
        return pd.DataFrame()

activities = get_activities_from_sheet()

class ContentGenerator:
    def __init__(self):
        # Use OpenAI gpt-5-nano reasoning model
        self.llm = ChatOpenAI(model="gpt-5-nano", temperature=1, max_tokens=40192, reasoning_effort="medium")
        self.embeddings: Embeddings = OpenAIEmbeddings()
        self.memory_db = self._load_memory()

    def _load_memory(self) -> Chroma:
        """Carga los documentos de memoria y crea una base de datos vectorial"""
        documents = []
        memory_path = path_manager.get_path('memory')

        # Función auxiliar para cargar un archivo
        def load_file(file_path: Path):
            try:
                if file_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                else:
                    loader = TextLoader(str(file_path))
                return loader.load()
            except Exception as e:
                safe_print(f"Error al cargar {file_path}: {str(e)}")
                return []

        # Cargar todos los archivos soportados
        for ext in ["*.txt", "*.pdf"]:
            for file_path in memory_path.glob(ext):
                docs = load_file(file_path)
                if docs:
                    documents.extend(docs)
                    safe_print(f"Archivo cargado exitosamente: {file_path}")

        if not documents:
            raise ValueError("No se encontraron documentos válidos en la carpeta memory/")

        safe_print(f"Total de documentos cargados: {len(documents)}")
        return Chroma.from_documents(documents, self.embeddings)

    def generate_content_plan(self, state: State, posts_per_day: int = 3) -> dict:
        context = self.memory_db.similarity_search(
            "temas principales del colectivo", k=3
        )

        # Obtener efemérides y noticias
        ephemerides = get_ephemerides(state["current_date"])
        news = get_news_for_date(state["current_date"])

        # Get configurable system message
        system_message = config_manager.get_setting('prompts', {}).get('system_message',
            """Eres un experto en comunicación social para el Colectivo Ambiental de Usaca (CAUSA), una organización ambiental y social de Bogotá, Colombia.

Tu misión es crear contenido para redes sociales que:
- Promueva la conciencia ambiental y los derechos de los animales
- Eduque sobre temas sociales y políticos relevantes
- Fomente la participación ciudadana en temas locales de Usaquén y Bogotá
- Mantenga un tono informativo, propositivo y esperanzador
- Use hashtags relevantes en español

El colectivo se enfoca en: medio ambiente, animalismo, derechos humanos, urbanismo sostenible, política local, cultura y memoria histórica.""")

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                system_message + """

                Debes crear publicaciones relevantes considerando:
                1. Noticias actuales de Colombia, Bogotá y Usaquén que sean relevantes para el colectivo.
                2. Efemérides importantes relacionadas con los temas del colectivo.
                3. Publicaciones para actividades del colectivo confirmadas.

                Genera {posts_per_day} publicaciones para la fecha: {current_date}

                ACTIVIDADES DEL COLECTIVO:
                {activities}
                ------------------------------------------------------------------------------------------------

                EFEMÉRIDES ENCONTRADAS PARA HOY:
                {ephemerides}
                ------------------------------------------------------------------------------------------------

                NOTICIAS ENCONTRADAS PARA HOY:
                {news}
                ------------------------------------------------------------------------------------------------

                NOTA: Las publicaciones deben ser relevantes para el colectivo y para la fecha actual. Puedes combinar noticias, efemérides y temas del colectivo. O dos publicaciones de noticias y una de efemérides. O dos noticias y una de temas del colectivo si no hay efemérides, o tres noticias si no hay efemérides ni actividades. Se creativo y profesional.

                El contenido debe incluir:
                - Un título llamativo y relevante para la publicación.(campo titulo)
                - Una descripción detallada de la imagen que se debe usar. Sé específico y detallado. (campo imagen) Para publicaciones de eventos, anuncios o que requieran texto, la descripción debe incluir instrucciones claras para que el generador de imágenes (DALL-E 3) pueda crear un flyer o una imagen con texto. Por ejemplo: 'Un flyer para un evento con el título "Nombre del Evento", la fecha "DD/MM/YYYY", y el lugar "Lugar del Evento". El estilo debe ser...'. Para otras publicaciones, puedes describir una imagen sin texto. Sé muy específico sobre los elementos visuales y el texto a incluir.
                - Un texto completo para la publicación que incluya hashtags relevantes (campo descripcion), incluye emojis y buenas prácticas de redacción para redes sociales.

                Contexto del colectivo:
                {context}

                IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido, sin texto adicional antes o después. Estructura requerida:
                ```json
                {{
                  "posts": [
                    {{
                      "fecha": "YYYY-MM-DD",
                      "titulo": "Título de la publicación",
                      "imagen": "Descripción detallada de la imagen",
                      "descripcion": "Contenido completo con hashtags"
                    }}
                  ]
                }}
                ```

                PROCESO DE GENERACIÓN:
                1. Genera {posts_per_day} publicaciones para la fecha actual.
                2. Revisa que las fechas de las publicaciones coincidan con las fechas de las efemérides o las actividades del colectivo. Ejemplo: observa que la fecha de la publicación 2024-11-28 no coincide con la fecha de la efeméride que es el 27 de noviembre, por lo tanto no la publicas.
                3. Revisa que las descripciones de las imágenes sean detalladas y profesionales.
                4. Revisa que los títulos y descripciones estén alineados con los valores y temas del colectivo.
                5. Revisa que las publicaciones cumplan con los criterios establecidos.
                6. RESPONDE SOLO CON JSON VÁLIDO. No agregues explicaciones, comentarios o texto adicional.

                """
            )
        ])

        # Generar contenido
        response = self.llm.invoke(
            prompt.format(
                activities=activities.to_string(),
                ephemerides=ephemerides,
                news=news,
                context="\n".join(doc.page_content for doc in context),
                current_date=state["current_date"],
                posts_per_day=posts_per_day
            )
        )

        content = response.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)

        return {
            "posts": self._parse_response(content),
            "messages": [AIMessage(content=response.content)]
        }

    def _parse_response(self, content: str, save_csv: bool = False) -> List[ContentPost]:
        """Parse la respuesta del LLM usando el parser JSON robusto"""

        safe_print("\n=== Respuesta del LLM ===")
        safe_print(content)
        safe_print("\n=== Procesando con parser JSON ===")

        try:
            # Use the robust JSON parser
            csv_posts = parse_posts_from_llm_response(content)

            if not csv_posts:
                raise ValueError("No se pudieron extraer posts válidos de la respuesta")

            # Convert to ContentPost format
            posts = []
            for post_data in csv_posts:
                post = ContentPost(
                    fecha=post_data['fecha'],
                    titulo=post_data['titulo'],
                    imagen=post_data['imagen'],
                    descripcion=post_data['descripcion']
                )
                posts.append(post)

            safe_print(f"✅ Se procesaron {len(posts)} posts exitosamente")

            if save_csv:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = path_manager.get_path('publicaciones') / f"social_media_calendar_{timestamp}.csv"

                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(['fecha', 'titulo', 'imagen', 'descripcion'])
                    for post in posts:
                        writer.writerow([
                            post['fecha'],
                            post['titulo'],
                            post['imagen'],
                            post['descripcion']
                        ])
                safe_print(f"✅ Calendario guardado en: {output_file}")

            return posts

        except Exception as e:
            safe_print(f"❌ Error al procesar respuesta: {e}")
            safe_print(f"Tipo de error: {type(e).__name__}")
            safe_print(f"Contenido problemático (primeros 500 chars):\n{content[:500]}")
            if len(content) > 500:
                safe_print(f"...contenido truncado ({len(content)} chars total)")
            raise ValueError(f"Error al procesar la respuesta: {str(e)}")

class ContentReviewer:
    def __init__(self, content_generator: ContentGenerator):
        # Use OpenAI gpt-5-nano reasoning model
        self.llm = ChatOpenAI(model="gpt-5-nano", temperature=1, max_tokens=40192, reasoning_effort="medium")
        self.embeddings: Embeddings = OpenAIEmbeddings()
        self.memory_db = None
        self.content_generator = content_generator

    def set_memory_db(self, memory_db: Chroma):
        self.memory_db = memory_db

    def review_content(self, state: State, posts_per_day: int = 3) -> dict:
        """Revisa y corrige el contenido generado"""
        if not state.get("posts"):
            return {}

        # Obtener contexto y efemérides
        context = self.memory_db.similarity_search(
            "temas principales del colectivo", k=5
        ) if self.memory_db else []

        ephemerides = get_ephemerides(state["current_date"])
        news = get_news_for_date(state["current_date"])

        # Get configurable review prompt (keeping it simple for now)
        review_prompt = """Eres un editor experto del Colectivo CAUSA. Revisa y corrige las publicaciones siguiendo estos criterios:

1. Validar fechas de efemérides y actividades
2. Validar alineación con la memoria del colectivo
3. Asegurar descripciones de imágenes detalladas y profesionales

Contexto del colectivo: {context}
Calendario de actividades: {activities}
Efemérides encontradas: {ephemerides}
Noticias encontradas: {news}
Publicaciones a revisar: {current_posts}
Fecha actual: {current_date}

IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido.
Estructura: {{"posts": [{{"fecha": "YYYY-MM-DD", "titulo": "...", "imagen": "...", "descripcion": "..."}}]}}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", review_prompt)
        ])

        # Format current posts as JSON for easier processing
        current_posts_list = []
        for post in state["posts"]:
            current_posts_list.append({
                "fecha": post["fecha"],
                "titulo": post["titulo"],
                "imagen": post["imagen"],
                "descripcion": post["descripcion"]
            })

        current_posts = json.dumps({
            "posts": current_posts_list
        }, indent=2, ensure_ascii=False)

        response = self.llm.invoke(
            prompt.format(
                context="\n".join(doc.page_content for doc in context),
                activities=activities.to_string(),
                ephemerides=ephemerides,
                news=news,
                current_posts=current_posts,
                current_date=state["current_date"]
            )
        )

        content = response.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)

        revised_posts = self.content_generator._parse_response(content, save_csv=True)

        return {
            "posts": revised_posts,
            "messages": state.get("messages", [])
        }

def create_content_graph(posts_per_day: int = 3) -> StateGraph:
    workflow = StateGraph(State)

    content_gen = ContentGenerator()
    content_reviewer = ContentReviewer(content_gen)
    content_reviewer.set_memory_db(content_gen.memory_db)

    # Create wrapper functions to pass posts_per_day
    def generate_with_config(state: State) -> dict:
        return content_gen.generate_content_plan(state, posts_per_day)

    def review_with_config(state: State) -> dict:
        return content_reviewer.review_content(state, posts_per_day)

    workflow.add_node("generate_content", generate_with_config)
    workflow.add_node("review", review_with_config)

    workflow.set_entry_point("generate_content")
    workflow.add_edge("generate_content", "review")
    workflow.add_edge("review", END)

    return workflow

def generate_social_media_calendar(days: int = 7, posts_per_day: int = 3) -> List[ContentPost]:
    graph = create_content_graph(posts_per_day).compile()
    start_date = datetime.now()
    posts = []

    for i in range(days):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")

        result = graph.invoke({
            "messages": [],
            "posts": [],
            "memory_docs": "",
            "current_date": current_date
        })

        if "posts" in result:
            posts.extend(result["posts"])

    return posts

if __name__ == "__main__":
    setup_directories()

    calendar = generate_social_media_calendar(days=8)
    safe_print("\n=== Calendario de Contenido ===\n")
    for post in calendar:
        safe_print(f"Fecha: {post['fecha']}")
        safe_print(f"Título: {post['titulo']}")
        safe_print(f"Imagen: {post['imagen']}")
        safe_print(f"Descripción: {post['descripcion']}")
        safe_print("\n" + "="*50 + "\n")

    safe_print("\nPara generar las imágenes, ejecute: python images.py")
