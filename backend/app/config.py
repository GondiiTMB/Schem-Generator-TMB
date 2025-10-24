from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    data_dir: Path = Field(default=Path("data"))
    dataset_dir: Path = Field(default=Path("data/dataset"))
    generated_dir: Path = Field(default=Path("data/generated"))
    model_dir: Path = Field(default=Path("data/model"))
    metadata_file: Path = Field(default=Path("data/dataset/metadata.json"))
    vocab_file: Path = Field(default=Path("data/model/palette.json"))
    text_vocab_file: Path = Field(default=Path("data/model/text_tokens.json"))
    training_state_file: Path = Field(default=Path("data/model/training_state.json"))

    class Config:
        env_prefix = "SCHEM_"


settings = Settings()
for directory in [
    settings.data_dir,
    settings.dataset_dir,
    settings.generated_dir,
    settings.model_dir,
]:
    directory.mkdir(parents=True, exist_ok=True)
