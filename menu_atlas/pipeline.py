import hashlib
import io
import os
from time import perf_counter
from uuid import uuid4
from PIL import Image, ImageOps
from pydantic import SecretStr
from prefect import flow, task, get_run_logger
from dotenv import load_dotenv
from .extraction import extract_image
from .quality import validate_menu
from .storage import persist
load_dotenv()

@task(name="Preparar imagem", persist_result=False)
def prepare_image(image_bytes: bytes) -> bytes:
    if len(image_bytes) > 20 * 1024 * 1024:
        raise ValueError("A imagem deve ter no máximo 20 MB.")
    with Image.open(io.BytesIO(image_bytes)) as image:
        if image.width * image.height > 40_000_000:
            raise ValueError("Imagem acima de 40 megapixels.")
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((3200, 3200))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
    get_run_logger().info("Imagem preparada para extração")
    return buf.getvalue()

@task(name="Extrair e estruturar com Gemini", persist_result=False)
def extract(image: bytes, api_key: SecretStr | None, model: str | None):
    result = extract_image(image, api_key.get_secret_value() if api_key else None, model)
    get_run_logger().info("Extraídos %s itens", len(result["menu"]["items"]))
    return result

@task(name="Validar com Great Expectations", persist_result=False)
def validate(menu, max_price):
    return validate_menu(menu, max_price)

@task(name="Persistir SQLite", persist_result=False)
def store(db_path, run, started):
    return persist(db_path, run, started)

@flow(name="Menu Atlas • Extração de cardápio", persist_result=False)
def process_menu(image_bytes: bytes, source: str = "upload", db_path: str | None = None,
                 api_key: SecretStr | None = None, model: str | None = None, max_price: float | None = None):
    started = perf_counter()
    path = db_path or os.getenv("DB_PATH", "data/menu_atlas.sqlite")
    run = {"id": str(uuid4()), "source": source, "sha256": hashlib.sha256(image_bytes).hexdigest()}
    try:
        image = prepare_image(image_bytes)
        result = extract(image, api_key, model)
        quality = validate(result["menu"], max_price or float(os.getenv("MAX_REASONABLE_PRICE", "1000")))
        run.update(extraction=result, quality=quality, status="review" if quality["needs_review"] else "valid")
    except Exception as exc:
        # Não armazena mensagens do provedor que possam conter URLs ou credenciais.
        run.update(status="failed", error=f"Falha no processamento ({type(exc).__name__}). Verifique chave, modelo, conexão e formato da imagem.")
        get_run_logger().error("Falha no processamento: %s", type(exc).__name__)
    return store(path, run, started)
