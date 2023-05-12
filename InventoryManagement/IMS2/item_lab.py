import unicodedata

class Item:
    def __init__(self, item_id, item_name, category_id):
        self.item_id = item_id
        self.item_name = item_name
        self.category_id = category_id

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


class SKU:
    def __init__(self, sku_id, sku_qty, item_id,
                 item_size_id, item_side_id, expiration_date):
        self.sku_id = sku_id
        self.sku_qty = sku_qty
        self.item_id = item_id
        self.item_size_id = item_size_id
        self.item_side_id = item_side_id
        self.expiration_date = expiration_date

    def name(self):

if __name__ == "__main__":
