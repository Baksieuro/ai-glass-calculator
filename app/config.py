from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Glass Calculator"
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = Path(__file__).parent / "data"
    MODEL: str = "qwen" # options: qwen, chatgpt, gigachat
    
    ASSETS_DIR: Path = Path(__file__).parent / "assets"
    LOGO_DIR: Path = ASSETS_DIR / "logo"
    WORKS_DIR: Path = ASSETS_DIR / "works"
    
    # Ограничения размеров товаров из products.txt
    MAX_HEIGHT_MM: int = 1605
    MAX_WIDTH_MM: int = 2750

    class Config:
        env_file = ".env"


settings = Settings()