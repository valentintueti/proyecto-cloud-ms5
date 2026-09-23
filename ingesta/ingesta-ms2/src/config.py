from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    S3_BUCKET: str
    AWS_REGION: str

    class Config:
        env_file = ".env"


settings = Settings()