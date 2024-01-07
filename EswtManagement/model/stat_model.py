import re
import pandas as pd
from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from db.db_utils import QtDbUtil
from common.d_logger import Logs
from db.ds_lab import Lab


logger = Logs().get_logger("main")


class Stats:
    def __init__(self):
        self.db_util = QtDbUtil()
        self.max_stats_count = 1000
        self.sessions_df = pd.DataFrame()

    def init_df(self, beg_date: QDate, end_date: QDate):
        self.beg_date = beg_date
        self.end_date = end_date

        beg_ts = self.beg_date.toString("yyyy-MM-dd")
        end_ts = self.end_date.addDays(1).toString("yyyy-MM-dd")

        main_part = f"SELECT * FROM sessions "
        time_part = f"WHERE timestamp >= '{beg_ts}' AND timestamp <= '{end_ts}' "
        limit_part = f"ORDER BY session_id DESC LIMIT {self.max_stats_count}"
        query = main_part + time_part + limit_part

        records = self.db_util.query(query)
        col_names = records['field_names']
        values = records['values']

        sess_df = pd.DataFrame(values, columns=col_names)
        provider_df = Lab().table_df['providers']
        modality_df = Lab().table_df['modalities']
        sess_df = pd.merge(sess_df, provider_df, on="provider_id")
        self.sessions_df = pd.merge(sess_df, modality_df, on="modality_id")
        logger.debug(self.sessions_df)

    def by_provider(self):
        columns = ['provider_id', 'modality_id', 'session_price']
        provider_df = self.sessions_df.loc[:, columns]
        provider_df.loc[:, 'count'] = 1
        grp_by_provider = provider_df.groupby(['provider_id', 'modality_id'])
        print(grp_by_provider.sum())

    def pivot_table(self):
        pivot_df = self.sessions_df.pivot_table(index=['provider_name'],
                                                columns='modality_name',
                                                values=['session_price'],
                                                aggfunc=['count', 'sum'])
        pivot_df.columns = [a[2]+"_"+a[0] for a in pivot_df.columns.to_flat_index()]
        print(pivot_df)



if __name__ == '__main__':
    stat = Stats()
    stat.init_df(QDate(2023, 10, 1), QDate(2023, 12, 20))
    stat.by_provider()
    stat.pivot_table()