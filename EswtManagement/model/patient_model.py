import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
from constants import RowFlags
from ds_exceptions import DuplicatePatientEmrId


logger = Logs().get_logger("main")


class PatientModel(DataModel):
    def __init__(self, user_name: str):
        self.init_params()
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('patients')

        self.col_edit_lvl = {
            'patient_id': EditLevel.NotEditable,
            'patient_emr_id': EditLevel.AdminModifiable,
            'patient_name': EditLevel.AdminModifiable,
            'patient_gender': EditLevel.AdminModifiable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_add_on_cols(self) -> None:
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['flag'] = RowFlags.OriginalRow

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        columns_for_delegate = ['patient_name', 'patient_gender']
        delegate_info = [self.get_col_number(c) for c in columns_for_delegate]
        return delegate_info

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        delegate_info = {
            self.get_col_number('patient_gender'): ["M", "F"]
        }
        return delegate_info

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        col_name = self.get_col_name(index.column())
        data_to_display = self.model_df.iloc[index.row(), index.column()]
        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            return str(data_to_display)
        elif role == Qt.TextAlignmentRole:
            left_aligned = ['description']
            if col_name in left_aligned:
                return Qt.AlignLeft
            else:
                return Qt.AlignCenter
        else:
            return super().data(index, role)

    def setData(self,
                index: QModelIndex,
                value: object,
                role=Qt.EditRole):
        """
        Override method from QAbstractTableModel
        :param index:
        :param value:
        :param role:
        :return:
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f"index({index}), value({value})")

        return super().setData(index, value, role)

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        """
        Needs to be implemented in subclasses
        :return: new dataframe if succeeds, otherwise raise an exception
        """
        emr_id: int = kwargs.get('patient_emr_id')
        duplicate_emr_id = self.model_df.query(f"patient_emr_id == {emr_id}")
        if not duplicate_emr_id.empty():
            error = f"patient_emr_id({emr_id}) is duplicate"
            raise DuplicatePatientEmrId(error)

        try:
            name: str = kwargs.get('patient_name')
            gender: str = kwargs.get('patient_gender')

            new_model_df = pd.DataFrame([{
                'patient_emr_id': emr_id,
                'patient_name': name,
                'patient_gender': gender,
                'flag': RowFlags.NewRow
            }])
            return new_model_df
        except Exception as e:
            logger.debug("New patient info is improper!")
            logger.debug(e)
