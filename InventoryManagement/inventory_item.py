import unicodedata


class InvItem:
    def __init__(self, handler, code, name, inventory):
        self.handler = handler
        self.code = code
        self.name = name
        self.inventory = inventory

    def get_name(self):
        return self.name

    def get_inventory(self):
        return self.inventory

    def update_inventory(self, quan):
        temp = self.inventory
        temp += quan
        if temp < 0:
            print("입력한 수량 보다 재고가 부족 하여 명령을 실행할 수 없습니다")
            return
        self.inventory = temp
        return self.inventory

    def fill_str_with_space(self, input_s="", max_size=40, fill_char="."):
        """
        - 길이가 긴 문자는 2칸으로 체크하고, 짧으면 1칸으로 체크함.
        - 최대 길이(max_size)는 40이며, input_s의 실제 길이가 이보다 짧으면
        남은 문자를 fill_char로 채운다.
        """
        l = 0
        for c in input_s:
            if unicodedata.east_asian_width(c) in ['F', 'W']:
                l += 2
            else:
                l += 1
        return input_s + fill_char * (max_size - l)

    def __repr__(self):
        codestr = f'{self.code}'.ljust(10)
        # namestr = f'{self.name}'.ljust(20, '.')
        namestr = self.fill_str_with_space(f'{self.name}', max_size=20)
        invstr = f'{self.inventory}'.rjust(10)
        return codestr + namestr + invstr
