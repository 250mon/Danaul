import os
import pandas as pd
from di_lab import Lab
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class EmrTransactionReader():
    def __init__(self, filename, parent):
        self.parent = parent
        self.filename = filename

    def read_df_from(self, code_df: pd.DataFrame) -> pd.DataFrame or None:
        try:
            bit_df = pd.read_excel(self.filename, sheet_name="처방 횟수 통계")
            bit_df = bit_df.loc[:,  ['처방코드', '총계']]
            for row in code_df.itertuples():
                code_list = row.bit_code.split(',')
                bit_df.loc[bit_df['처방코드'].isin(code_list), 'sku_id'] = row.sku_id

            # bit_df.sku_id.dtype is float64 because it includes np.nan
            bit_df = bit_df.dropna().astype({"sku_id": "int64"})
            # the result is a dataframe whose index is db_code and name is 총계
            bit_df = bit_df.groupby(by=['sku_id'], dropna=True).sum().loc[:, ["총계"]]
            bit_df = bit_df.rename(columns={"총계": "tr_qty"})
            sku_df = self.parent.sku_model.model_df[["sku_id", "item_name"]]
            ret_df = pd.merge(bit_df, sku_df, left_index=True, right_on="sku_id")
            logger.debug(f"\n{ret_df}")
            return ret_df
        except Exception as e:
            logger.error(e)
            return None

    # def read_df_from(self, codes: List) -> pd.DataFrame or None:
    #     try:
    #         bit_df = pd.read_excel(self.filename, sheet_name="처방 횟수 통계")
    #         bit_df = bit_df.loc[:,  ['처방코드', '총계']]
    #         for code in codes:
    #             code_list = code.split(',')
    #             bit_df.loc[bit_df['처방코드'].isin(code_list), 'bit_code'] = code
    #
    #         # the result is a dataframe whose index is db_code and name is 총계
    #         bit_df = bit_df.groupby(by=['bit_code'], dropna=True).sum().loc[:, ["총계"]]
    #         bit_df = bit_df.rename(columns={"총계": "tr_qty"})
    #         logger.debug(f"\n{bit_df}")
    #         return bit_df
    #     except Exception as e:
    #         logger.error(e)
    #         return None


if __name__ == "__main__":
    reader = EmrTransactionReader("bit_doc.xlsx")
    result = reader.read_df_from(['noci40,noci40_fr', 'noci120,noci120_fr'])
    print(result)

