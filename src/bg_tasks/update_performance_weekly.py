import logging
import uuid
from datetime import datetime, timedelta

import pandas as pd
import pendulum
import seqlog
from sqlmodel import Session, select
from web3 import Web3
from core import constants

from bg_tasks.utils import (
    calculate_pps_statistics,
    calculate_roi,
    get_before_price_per_shares,
)
from core.abi_reader import read_abi
from core.config import settings
from core.db import engine
from models import Vault
from models.pps_history import PricePerShareHistory
from models.vault_performance import VaultPerformance
from schemas.fee_info import FeeInfo
from schemas.vault_state import VaultState
from services.market_data import get_price

if settings.SEQ_SERVER_URL is not None or settings.SEQ_SERVER_URL != "":
    seqlog.configure_from_file("./config/seqlog.yml")

# # Initialize logger
logger = logging.getLogger("options_wheel_update_performance_weekly")
logger.setLevel(logging.INFO)

# Connect to the Ethereum network
if settings.ENVIRONMENT_NAME == "Production":
    w3 = Web3(Web3.HTTPProvider(settings.ARBITRUM_MAINNET_INFURA_URL))
else:
    w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_TESTNET_INFURA_URL))

token_abi = read_abi("ERC20")
rockonyx_stablecoin_vault_abi = read_abi("RockOnyxStableCoin")
rockOnyxUSDTVaultContract = w3.eth.contract(
    address=settings.ROCKONYX_STABLECOIN_ADDRESS, abi=rockonyx_stablecoin_vault_abi
)

session = Session(engine)


def balance_of(wallet_address, token_address):
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    token_balance = token_contract.functions.balanceOf(wallet_address).call()
    return token_balance


def get_price_per_share_history(vault_id: uuid.UUID) -> pd.DataFrame:
    pps_history = session.exec(
        select(PricePerShareHistory)
        .where(PricePerShareHistory.vault_id == vault_id)
        .order_by(PricePerShareHistory.datetime.asc())
    ).all()

    # Convert the list of PricePerShareHistory objects to a DataFrame
    pps_history_df = pd.DataFrame([vars(pps) for pps in pps_history])

    return pps_history_df[["datetime", "price_per_share", "vault_id"]]


def update_price_per_share(vault_id: uuid.UUID, current_price_per_share: float):
    today = datetime.now().date()

    # Check if a PricePerShareHistory record for today already exists
    existing_pps = session.exec(
        select(PricePerShareHistory).where(
            PricePerShareHistory.vault_id == vault_id,
            PricePerShareHistory.datetime == today,
        )
    ).first()

    if existing_pps:
        # If a record for today already exists, update the price per share
        existing_pps.price_per_share = current_price_per_share
    else:
        # If no record for today exists, create a new one
        new_pps = PricePerShareHistory(
            datetime=today, price_per_share=current_price_per_share, vault_id=vault_id
        )
        session.add(new_pps)

    session.commit()


def get_current_pps():
    pps = rockOnyxUSDTVaultContract.functions.pricePerShare().call()
    return pps / 1e6


def get_current_round():
    current_round = rockOnyxUSDTVaultContract.functions.getCurrentRound().call()
    return current_round


def get_current_tvl():
    tvl = rockOnyxUSDTVaultContract.functions.totalValueLocked().call()
    return tvl / 1e6


def get_fee_info():
    # fee_structure = rockOnyxUSDTVaultContract.functions.getFeeInfo().call()
    fee_structure = [0, 0, 10, 1]
    fee_info = FeeInfo(
        deposit_fee=fee_structure[0],
        exit_fee=fee_structure[1],
        performance_fee=fee_structure[2],
        management_fee=fee_structure[3],
    )
    json_fee_info = fee_info.model_dump_json()
    return json_fee_info


def get_vault_state(owner_wallet_address: str):
    state = rockOnyxUSDTVaultContract.functions.getVaultState().call(
        {"from": owner_wallet_address}
    )
    vault_state = VaultState(
        performance_fee=state[0] / 1e6,
        management_fee=state[1] / 1e6,
        current_round_fee=state[2] / 1e6,
        withdrawal_pool=state[3] / 1e6,
        pending_deposit=state[4] / 1e6,
        total_share=state[5] / 1e6,
        last_locked=state[6] / 1e6,
    )
    return vault_state


def get_next_friday():
    today = datetime.today()
    next_friday = today + timedelta((4 - today.weekday()) % 7)
    next_friday = next_friday.replace(hour=8, minute=0, second=0, microsecond=0)
    return next_friday


def calculate_apy_ytd(vault_id, current_price_per_share):
    now = datetime.now()
    vault = session.exec(select(Vault).where(Vault.id == vault_id)).first()

    # Get the start of the year or the first logged price per share
    start_of_year = datetime(now.year, 1, 1)
    price_per_share_start = session.exec(
        select(PricePerShareHistory)
        .where(
            PricePerShareHistory.vault_id == vault.id
            and PricePerShareHistory.datetime >= start_of_year
        )
        .order_by(PricePerShareHistory.datetime.asc())
    ).first()

    prev_pps = price_per_share_start.price_per_share if price_per_share_start else 1

    # Calculate the APY
    apy_ytd = calculate_roi(
        current_price_per_share,
        prev_pps,
        days=(now - price_per_share_start.datetime).days,
    )

    return apy_ytd


# Step 4: Calculate Performance Metrics
def calculate_performance(vault_id: uuid.UUID, owner_address: str):
    current_price = get_price("ETHUSDT")

    # today = datetime.strptime(df["Date"].iloc[-1], "%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # candles = get_klines("ETHUSDT", end_time=(today + timedelta(days=2)), limit=1)
    # current_price = float(candles[0][4])

    # price_per_share_df = get_price_per_share_history(vault_id)

    current_price_per_share = get_current_pps()
    total_balance = get_current_tvl()
    fee_info = get_fee_info()
    vault_state = get_vault_state(owner_address)
    # Calculate Monthly APY
    month_ago_price_per_share = get_before_price_per_shares(session, vault_id, days=30)
    month_ago_datetime = pendulum.instance(month_ago_price_per_share.datetime).in_tz(
        pendulum.UTC
    )
    days = min((pendulum.now(tz=pendulum.UTC) - month_ago_datetime).days, 30)
    monthly_apy = calculate_roi(
        current_price_per_share, month_ago_price_per_share.price_per_share, days=days
    )

    week_ago_price_per_share = get_before_price_per_shares(session, vault_id, days=7)
    week_ago_datetime = pendulum.instance(week_ago_price_per_share.datetime).in_tz(
        pendulum.UTC
    )
    days = min((pendulum.now(tz=pendulum.UTC) - week_ago_datetime).days, 7)
    weekly_apy = calculate_roi(
        current_price_per_share, week_ago_price_per_share.price_per_share, days=days
    )

    apy_ytd = calculate_apy_ytd(vault_id, current_price_per_share)

    performance_history = session.exec(
        select(VaultPerformance).order_by(VaultPerformance.datetime.asc()).limit(1)
    ).first()

    benchmark = current_price
    benchmark_percentage = ((benchmark / performance_history.benchmark) - 1) * 100
    apy_1m = monthly_apy * 100
    apy_1w = weekly_apy * 100
    apy_ytd = apy_ytd * 100

    all_time_high_per_share, sortino, downside, risk_factor = calculate_pps_statistics(
        session, vault_id
    )
    # Create a new VaultPerformance object
    performance = VaultPerformance(
        datetime=today,
        total_locked_value=total_balance,
        benchmark=benchmark,
        pct_benchmark=benchmark_percentage,
        apy_1m=apy_1m,
        apy_1w=apy_1w,
        apy_ytd=apy_ytd,
        vault_id=vault_id,
        risk_factor=risk_factor,
        all_time_high_per_share=all_time_high_per_share,
        total_shares=vault_state.total_share,
        sortino_ratio=sortino,
        downside_risk=downside,
        earned_fee=vault_state.performance_fee + vault_state.management_fee,
        fee_structure=fee_info,
    )
    update_price_per_share(vault_id, current_price_per_share)

    return performance


# Main Execution
def main():
    try:
        # Get the vault from the Vault table with name = "Stablecoin Vault"
        vault = session.exec(
            select(Vault).where(Vault.strategy_name == constants.OPTIONS_WHEEL_STRATEGY)
        ).first()

        new_performance_rec = calculate_performance(vault.id, vault.owner_wallet_address)
        # Add the new performance record to the session and commit
        session.add(new_performance_rec)

        # Update the vault with the new information
        vault.ytd_apy = new_performance_rec.apy_ytd
        vault.monthly_apy = new_performance_rec.apy_1m
        vault.weekly_apy = new_performance_rec.apy_1w
        # vault.current_round = get_current_round()
        vault.current_round = 1  # TODO: Remove this line once the contract is updated
        vault.next_close_round_date = get_next_friday()

        session.commit()
    except Exception as e:
        logger.error(
            "An error occurred while updating the performance metrics: %s",
            e,
            exc_info=True,
        )


if __name__ == "__main__":
    main()
