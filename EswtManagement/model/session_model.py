import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from db.ds_lab import Lab
from common.d_logger import Logs
from constants import EditLevel
from common.datetime_utils import *
from constants import RowFlags
from ds_exceptions import *

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
logger = Logs().get_logger("main")


class SessionModel(DataModel):
    def __init__(self, user_name: str):
        self.init_params()
        self.selected_patient_id = None
        self.selected_patient_name = ""
        self.beg_timestamp = QDate.currentDate().addMonths(-6)
        self.end_timestamp = QDate.currentDate()
        # setting a model is carried out in the DataModel
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('sessions')

        self.col_edit_lvl = {
            'session_id': EditLevel.NotEditable,
            'patient_id': EditLevel.NotEditable,
            'patient_emr_id': EditLevel.NotEditable,
            'patient_name': EditLevel.NotEditable,
            'provider_id': EditLevel.NotEditable,
            'provider_name': EditLevel.UserModifiable,
            'modality_id': EditLevel.NotEditable,
            'modality_name': EditLevel.UserModifiable,
            'part_id': EditLevel.NotEditable,
            'part_name': EditLevel.UserModifiable,
            'description': EditLevel.UserModifiable,
            'timestamp': EditLevel.NotEditable,
            'session_price': EditLevel.UserModifiable,
            'user_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        self.model_df = Lab().table_df['sessions']

        # set more columns for the view
        patient_df = Lab().table_df['patients']
        pt_info = patient_df.loc[:, ['patient_id', 'patient_emr_id', 'patient_name']]
        self.model_df = self.model_df.merge(pt_info, how='left', on='patient_id')

        user_df = Lab().table_df['users']
        provider_df = user_df.query("user_job == '물리치료'")
        self.provider_info = provider_df.loc[:, ['user_id', 'active', 'user_realname']]
        self.provider_info.rename(columns={'user_id': 'provider_id',
                                           'user_realname': 'provider_name'},
                                  inplace=True)
        self.model_df = self.model_df.merge(self.provider_info, how='left', on='provider_id')

        modality_df = Lab().table_df['modalities']
        self.modality_info = modality_df.loc[:, ['modality_id', 'modality_name']]
        self.model_df = self.model_df.merge(self.modality_info, how='left', on='modality_id')

        part_df = Lab().table_df['body_parts']
        self.part_info = part_df.loc[:, ['part_id', 'part_name']]
        self.model_df = self.model_df.merge(self.part_info, how='left', on='part_id')

        user_info = user_df.loc[:, ['user_id', 'user_name']]
        self.model_df = self.model_df.merge(user_info, how='left', on='user_id')

        self.model_df['flag'] = RowFlags.OriginalRow

    def set_upper_model_id(self, patient_id: int or None):
        self.selected_patient_id = patient_id
        logger.debug(f"patient_id({self.selected_patient_id}) is set")

        if patient_id is not None:
            pt_df = Lab().table_df['patients']
            self.selected_patient_name = Lab().get_data_from_id('patients',
                                                                patient_id,
                                                                'patient_name')
            logger.debug(f"patient({self.selected_patient_name}) is set")
        else:
            self.selected_patient_name = ""

    def set_beg_timestamp(self, beg: QDate):
        self.beg_timestamp = beg
        logger.debug(f"beg_timestamp({self.beg_timestamp})")

    def set_end_timestamp(self, end: QDate):
        self.end_timestamp = end
        logger.debug(f"end_timestamp({self.end_timestamp})")

    async def update(self):
        """
        Override method to use selected_patient_id and begin_/end_ timestamp
        :return:
        """
        # end day needs to be added 1 day otherwise query results only includes those thata
        # were created until the day 00h 00mm 00sec
        logger.debug(f"downloading data from DB")
        kwargs = {'patient_id': self.selected_patient_id,
                  'beg_timestamp': self.beg_timestamp.toString("yyyy-MM-dd"),
                  'end_timestamp': self.end_timestamp.addDays(1).toString("yyyy-MM-dd")}
        logger.debug(f"\n{kwargs}")
        await super().update(**kwargs)

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in ['description']]
        return default_info_list

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        provider_list = Lab().table_df['active_providers']['provider_name'].to_list()
        modality_list = self.modality_info['modality_name'].to_list()
        part_list = self.part_info['part_name'].to_list()

        combo_info_dict = {
            self.get_col_number('provider_name'): provider_list,
            self.get_col_number('modality_name'): modality_list,
            self.get_col_number('part_name'): part_list,
        }
        return combo_info_dict

    def get_spinbox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the spinbox
        for spinbox delegate
        :return:
        """
        spin_info_dict = {
            self.get_col_number('session_price'): [0, 1000000],
        }
        return spin_info_dict

    def is_active_row(self, idx: QModelIndex) -> bool:
        return True

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
            int_type_columns = ['session_id', 'patient_id', 'provider_id',
                                'modality_id', 'part_id', 'session_price', 'user_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)

            elif col_name == 'active':
                if data_to_display:
                    return 'Y'
                else:
                    return 'N'

            elif col_name == 'timestamp':
                # data type is datetime.date
                return pydt_to_qdt(data_to_display)

            else:
                # otherwise, string type
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

        col_name = self.get_col_name(index.column())
        if col_name == 'active':
            # taking care of converting str type input to bool type
            if value == 'Y':
                value = True
            else:
                value = False

        elif col_name == 'provider_name':
            id_col = self.get_col_number('provider_id')
            provider_id = Lab().get_id_from_data('active_provider', value, col_name)
            self.model_df.iloc[index.row(), id_col] = provider_id

        elif col_name == 'modality_name':
            id_col = self.get_col_number('modality_id')
            modality_id = Lab().get_id_from_data('modalities', value, col_name)
            self.model_df.iloc[index.row(), id_col] = modality_id

        elif col_name == 'part_name':
            id_col = self.get_col_number('part_id')
            part_id = Lab().get_id_from_data('body_parts', value, col_name)
            self.model_df.iloc[index.row(), id_col] = part_id

        elif col_name == 'timestamp':
            # data type is datetime.date
            if isinstance(value, QDateTime):
                value = qdt_to_pydt(value)

        return super().setData(index, value, role)

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        """
        :return: new dataframe if succeeds, otherwise raise an exception
        """
        if self.selected_patient_id is None:
            error = "patient_id is empty"
            raise NonExistentPatientIdError(error)

        # patients part
        patient_emr_id = Lab().get_data_from_id('patients',
                                                self.selected_patient_id,
                                                'patient_emr_id')
        patient_name = Lab().get_data_from_id('patients',
                                              self.selected_patient_id,
                                              'patient_name')
        # provider part
        provider_name = kwargs.get('provider_name')
        provider_id = Lab().get_id_from_data('active_providers',
                                             provider_name,
                                             'provider_name')
        # modality part
        modality_name = kwargs.get('modality_name')
        modality_id = Lab().get_id_from_data('modalities',
                                             modality_name,
                                             'modality_name')

        # body part
        part_name = kwargs.get('part_name')
        part_id = Lab().get_id_from_data('body_parts',
                                         part_name,
                                         'part_name')

        description = kwargs.get('description', "")
        session_price = kwargs.get('session_price', 0)
        user_id = Lab().user_id_s.loc[self.user_name]

        new_model_df = pd.DataFrame([{
            'patient_id': self.selected_patient_id,
            'patient_emr_id': patient_emr_id,
            'patient_name': patient_name,
            'provider_id': provider_id,
            'provider_name': provider_name,
            'modality_id': modality_id,
            'modality_name': modality_name,
            'part_id': part_id,
            'part_name': part_name,
            'description': description,
            'timestamp': datetime.now(),
            'session_price': session_price,
            'user_id': user_id,
            'flag': RowFlags.NewRow
        }])
        return new_model_df

    def validate_new_row(self, index: QModelIndex) -> bool:
        """
        This is used to validate a new row generated by SingleSessionWindow
        when a user is done with input for a new row, the window emits
        create_session_signal which triggers the session_widget to determine
        whether to drop the new row using this method
        If it returns True, the new row remains, otherwise drops
        :param index:
        :return:
        """
        return True
