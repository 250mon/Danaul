import unicodedata
from datetime import datetime


def _conv_date(_date: str) -> datetime:
    return datetime.strptime(_date, "%Y-%m-%d")


class Item:
    def __init__(self, item_id, item_name, category_id):
        self.item_id = item_id
        self.item_name = item_name
        self.category_id = category_id

    @property
    def item_id(self):
        return self._item_id

    @item_id.setter
    def item_id(self, val):
        self._item_id = val

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
    def __init__(self, sku_id, sku_qty, item_id,
                 item_size_id=1, item_side_id=1,
                 expiration_date: str = '9999-01-01'):
        self.sku_id = sku_id
        self.sku_qty = sku_qty
        self.item_id = item_id
        self.item_size_id = item_size_id
        self.item_side_id = item_side_id
        self.expiration_date = expiration_date

    @property
    def sku_id(self):
        return self._sku_id

    @sku_id.setter
    def sku_id(self, val):
        self._sku_id = val

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
    def expiration_date(self, val: str):
        self._expiration_date = _conv_date(val)


class Transaction:
    def __init__(self, tr_id, user_id, sku_id, tr_type_id,
                 tr_qty, before_qty, after_qty,
                 tr_date: str = datetime.today().strftime('%Y-%m-%d')):
        self.tr_id = tr_id
        self.user_id = user_id
        self.sku_id = sku_id
        self.tr_type_id = tr_type_id
        self.tr_qty = tr_qty
        self.before_qty = before_qty
        self.after_qty = after_qty
        self.tr_date = tr_date

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
    def tr_date(self) -> datetime:
        return self._tr_date

    @tr_date.setter
    def tr_date(self, val: str):
        self._tr_date = _conv_date(val)
