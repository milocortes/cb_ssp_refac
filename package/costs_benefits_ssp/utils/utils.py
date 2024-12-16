from typing import List
import os

def build_path(PATH : List[str]) -> str:
    return os.path.abspath(os.path.join(*PATH))

def get_tx_prefix(tx : str, ssp_txs : List[str]) -> str:

    tx_prefix = [ssp_tx for ssp_tx in ssp_txs if tx.startswith(ssp_tx)]

    if tx_prefix:
        return tx_prefix[0]
    else:
        print(f"The TX {tx} is missing on AttTransformationCode")

