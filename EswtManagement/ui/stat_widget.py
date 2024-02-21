import sys
import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QApplication, QTableView, QVBoxLayout
)
from PySide6.QtCore import QAbstractTableModel, QDate
from PySide6.QtGui import QStandardItemModel, QStandardItem
from common.d_logger import Logs
from db.db_utils import QtDbUtil
from db.ds_lab import Lab


logger = Logs().get_logger("main")


class StatTableModel(QAbstractTableModel):
    def __init__(self):
        self.db_util = QtDbUtil()
        self.max_stats_count = 1000
        self.sessions_df = pd.DataFrame()
        self.stat_df = None

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

    def pivot_table(self):
        self.stat_df = self.sessions_df.pivot_table(index=['provider_name'],
                                                    columns='modality_name',
                                                    values=['session_price'],
                                                    aggfunc=['count', 'sum'])
        self.stat_df.columns = [a[2]+"_"+a[0] for a in self.stat_df.columns.to_flat_index()]

    def get_df(self):
        return self.stat_df

class StatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.model = QStandardItemModel()
        self.initUi()

    def initUi(self):
        self.setWindowTitle("통계")
        self.stat_view = QTableView()
        self.stat_view.setModel(self.model)

        vbox = QVBoxLayout()
        vbox.addWidget(self.stat_view)

        self.setLayout(vbox)
        self.setMinimumSize(400, 400)
        self.setMaximumSize(600, 800)

    def load_df(self, data_df):
        self.model.setRowCount(data_df.shape[0])
        self.model.setColumnCount(data_df.shape[1])
        self.model.setHorizontalHeaderLabels(data_df.columns.to_list())
        self.model.setVerticalHeaderLabels(data_df.index.to_list())
        for i, row in enumerate(data_df.itertuples()):
            items = [QStandardItem(str(item)) for item in row[1:]]
            self.model.insertRow(i, items)


if __name__ == "__main__":
    raw_data = {'col0': [1, 2, 3, 4],
                'col1': [10, 20, 30, 40],
                'col2': [1000, 2000, 3000, 4000]}
    data = pd.DataFrame(raw_data)

    app = QApplication(sys.argv)
    stat = StatTableModel()
    stat.init_df(QDate(2023, 10, 1), QDate(2023, 12, 20))
    stat.pivot_table()
    data_df = stat.get_df()
    window = StatWidget()
    window.load_df(data_df)
    window.show()
    app.exec()
