import unicodedata
from datetime import datetime


class EtcData:
    def __init__(self, id: int, name: str):
        self.table = None
        self.id = id
        self.name = name

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, val):
        self._id = val

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

class Category(EtcData):
    def __init__(self, category_id: int, category_name: str):
        super().__init__(category_id, category_name)
        self.table = 'category'

class ItemSide(EtcData):
    def __init__(self, item_side_id: int, item_side: str):
        super().__init__(item_side_id, item_side)
        self.table = 'item_side'

class ItemSize(EtcData):
    def __init__(self, item_size_id: int, item_size: str):
        super().__init__(item_size_id, item_size)
        self.table = 'item_size'

class TransactionType(EtcData):
    def __init__(self, tr_type_id: int, tr_type: str):
        super().__init__(tr_type_id, tr_type)
        self.table = 'transaction_type'

class User(EtcData):
    def __init__(self, user_id: int, user_name: str):
        super().__init__(user_id, user_name)
        self.table = 'users'


class Item:
    def __init__(self, item_id: int, item_valid: bool,
                 item_name: str, category_id: int):
        self.table = 'items'
        self.item_id = item_id
        self.item_valid = item_valid
        self.item_name = item_name
        self.category_id = category_id

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, val):
        self._item_id = val

    @property
    def item_valid(self):
        return self._item_valid

    @item_valid.setter
    def item_valid(self, val):
        self._item_valid = val

    @property
    def item_name(self):
        return self._item_name

    @item_name.setter
    def item_name(self, val):
        self._item_name = val

    @property
    def category_id(self):
        return self._category_id

    @category_id.setter
    def category_id(self, val):
        self._category_id = val

    def fill_str_with_space(self, input_s="", max_size=40, fill_char="."):
        """
        길이가 긴 문자는 2칸으로 체크하고, 짧으면 1칸으로 체크함.
        최대 길이(max_size)는 40이며, input_s의 실제 길이가 이보다 짧으면
        남은 문자를 fill_char로 채운다.
        :param input_s:
        :param max_size:
        :param fill_char:
        :return:
        """
        l = 0
        for c in input_s:
            if unicodedata.east_asian_width(c) in ['F', 'W']:
                l += 2
            else:
                l += 1
        return input_s + fill_char * (max_size - l)

    def __repr__(self):
        id_str = f'{self.item_id}'.ljust(10)
        name_str = self.fill_str_with_space(f'{self.item_name}', max_size=20)
        cat_id_str = f'{self.category_id}'.rjust(10)
        return id_str + name_str + cat_id_str


class Sku:
    def __init__(self, sku_id: int, sku_valid: bool, bit_code: str,
                 sku_qty: int, min_qty: int, item_id: int,
                 item_size_id: int = 1, item_side_id: int = 1,
                 expiration_date=datetime.strptime('9999-01-01', "%Y-%m-%d"),
                 item_name: str = None, item_size: str = None,
                 item_side: str = None):
        self.table = 'skus'
        self.sku_id = sku_id
        self.sku_valid = sku_valid
        self.bit_code = bit_code
        self.sku_qty = sku_qty
        self.min_qty = min_qty
        self.item_id = item_id
        self.item_size_id = item_size_id
        self.item_side_id = item_side_id
        self.expiration_date = expiration_date

        # relation fields
        self.item_name = item_name
        self.item_size = item_size
        self.item_side = item_side

    @property
    def sku_id(self):
        return self._sku_id

    @sku_id.setter
    def sku_id(self, val):
        self._sku_id = val

    @property
    def sku_valid(self):
        return self._sku_valid

    @sku_valid.setter
    def sku_valid(self, val):
        self._sku_valid = val

    @property
    def bit_code(self):
        return self._bit_code

    @bit_code.setter
    def bit_code(self, val):
        self._bit_code = val

    @property
    def min_qty(self):
        return self._min_qty

    @min_qty.setter
    def min_qty(self, val):
        self._min_qty = val

    @property
    def sku_qty(self):
        return self._sku_qty

    @sku_qty.setter
    def sku_qty(self, val):
        self._sku_qty = val

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, val):
        self._item_id = val

    @property
    def item_size_id(self):
        return self._item_size_id

    @item_size_id.setter
    def item_size_id(self, val):
        self._item_size_id = val

    @property
    def item_side_id(self):
        return self._item_side_id

    @item_side_id.setter
    def item_side_id(self, val):
        self._item_side_id = val

    @property
    def expiration_date(self) -> datetime:
        return self._expiration_date

    @expiration_date.setter
    def expiration_date(self, val: datetime):
        self._expiration_date = val


class Transaction:
    def __init__(self, tr_id: int, user_id: int, sku_id: int,
                 tr_type_id: int, tr_qty: int, before_qty: int, after_qty: int,
                 tr_timestamp: datetime = datetime.now(), user: str = None,
                 tr_type: str = None, item_name: str = None, item_size: str = None,
                 item_side: str = None):
        self.table = 'transactions'
        self.tr_id = tr_id
        self.user_id = user_id
        self.sku_id = sku_id
        self.tr_type_id = tr_type_id
        self.tr_qty = tr_qty
        self.before_qty = before_qty
        self.after_qty = after_qty
        self.tr_timestamp = tr_timestamp

        # relation fields
        self.user = user
        self.tr_type = tr_type
        self.item_name = item_name
        self.item_size = item_size
        self.item_side = item_side

    @property
    def tr_id(self):
        return self._tr_id

    @tr_id.setter
    def tr_id(self, val):
        self._tr_id = val

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, val):
        self._user_id = val

    @property
    def sku_id(self):
        return self._sku_id

    @sku_id.setter
    def sku_id(self, val):
        self._sku_id = val

    @property
    def tr_type_id(self):
        return self._tr_type

    @tr_type_id.setter
    def tr_type_id(self, val):
        self._tr_type = val

    @property
    def tr_qty(self):
        return self._tr_qty

    @tr_qty.setter
    def tr_qty(self, val):
        self._tr_qty = val

    @property
    def before_qty(self):
        return self._before_qty

    @before_qty.setter
    def before_qty(self, val):
        self._before_qty = val

    @property
    def after_qty(self):
        return self._after_qty

    @after_qty.setter
    def after_qty(self, val):
        self._after_qty = val

    @property
    def tr_timestamp(self) -> datetime:
        return self._tr_timestamp

    @tr_timestamp.setter
    def tr_timestamp(self, val: datetime):
        self._tr_timestamp = val



