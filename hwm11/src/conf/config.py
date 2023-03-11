from pydantic import BaseSettings


class Settings(BaseSettings):

    sqlalchemy_database_url: str = "postgresql://user:password@localhost:5432/$postgres"
    secret_key_jwt: str = "secret_key"
    algorithm: str = "HS256"

    mail_username: str = "goithw13@meta.ua"
    mail_password: str = "Goithw13"
    mail_from: str = "goithw13@meta.ua"
    mail_port: int = 465
    mail_server: str = "smtp.meta.ua"

    redis_host: str = "localhost"
    redis: int = 6379

    cloudinary_name: str = "name"
    cloudinary_api_key: int = 512194773231647
    cloudinary_secret: str = "secret"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
