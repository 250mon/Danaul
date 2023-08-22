import os
import pandas as pd
from typing import List
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class EmrTransactionReader():
    def __init__(self, filename):
        self.filename = filename

    def read_df_from(self, codes: List) -> pd.DataFrame or None:
        try:
            bit_df = pd.read_excel(self.filename, sheet_name="처방 횟수 통계")
            bit_df = bit_df.loc[:,  ['처방코드', '총계']]
            for code in codes:
                code_list = code.split(',')
                bit_df.loc[bit_df['처방코드'].isin(code_list), 'bit_code'] = code

            # the result is a dataframe whose index is db_code and name is 총계
            bit_df = bit_df.groupby(by=['bit_code'], dropna=True).sum().loc[:, ["총계"]]
            logger.debug(f"read_df_from: \n{bit_df}")
            return bit_df

        except:
            return None


if __name__ == "__main__":
    reader = EmrTransactionReader("bit_doc.xlsx")
    result = reader.read_df_from(['noci40,noci40_fr', 'noci120,noci120_fr'])
    print(result)

