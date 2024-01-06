import secrets
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT_NAME: str

    @property
    def is_production(self):
        return self.ENVIRONMENT_NAME == "Production"

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    ETHER_MAINNET_INFURA_URL: str
    ARBITRUM_MAINNET_INFURA_URL: str = (
        "https://arbitrum-mainnet.infura.io/v3/85cde589ce754dafa0a57001c326104d"
    )
    WALLET_ADDRESS: str
    WSTETH_ADDRESS: str = "0x5979D7b546E38E414F7E9822514be443A4800529"
    USDC_ADDRESS: str = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    USDCE_ADDRESS: str = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"

    class Config:
        case_sensitive = True
        env_file = "../.env"


settings = Settings()