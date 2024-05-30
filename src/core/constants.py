from core.config import settings

RENZO = "renzo"
ZIRCUIT = "zircuit"
KELPDAO = "kelpdao"
EIGENLAYER = "eigenlayer"


OPTIONS_WHEEL_STRATEGY = "options_wheel_strategy"
DELTA_NEUTRAL_STRATEGY = "delta_neutral_strategy"

NETWORK_RPC_URLS = {
    "arbitrum_one": settings.ARBITRUM_MAINNET_INFURA_URL,
    "ethereum": settings.ETHER_MAINNET_INFURA_URL,
}

NETWORK_SOCKET_URLS = {
    "arbitrum_one": settings.ARBITRUM_MAINNET_INFURA_WEBSOCKER_URL,
    "ethereum": settings.ETHER_MAINNET_INFURA_URL,
}