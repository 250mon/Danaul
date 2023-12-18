import pandas as pd
from typing import Dict
from common.d_logger import Logs


logger = Logs().get_logger('main')


def get_col_number(df: pd.DataFrame, col_name: str) -> int:
    return df.columns.get_loc(col_name)


def get_col_name(df: pd.DataFrame, col_num: int) -> str:
    return df.columns[col_num]


def get_data_by_id(df: pd.DataFrame, id: int, col: str) -> object:
    ret_s = df.loc[df.iloc[:, 0] == id, col]
    if ret_s.empty:
        logger.debug(f'no data at col({col})for id({id})')
        return None
    else:
        return ret_s.item()


def get_id_by_data(df: pd.DataFrame,
                   data: Dict[str, object],
                   id_col_name: str) -> int or None:
    col, data = data.popitem()
    ret_s = df.loc[df.loc[:, col] == data, id_col_name]
    if ret_s.empty:
        logger.debug(f'no id for col({col}) data({data})')
        return None
    else:
        return ret_s.item()
