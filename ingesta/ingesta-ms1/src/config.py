from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    S3_BUCKET: str
    AWS_REGION: str

    class Config:
        env_file = ".env"


settings = Settings()