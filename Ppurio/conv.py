import pandas as pd
import os
import datetime

def conv_datetime(dt):
    weekdays = ('월', '화', '수', '목', '금', '토', '일')
    # dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    form_time_str = dt.strftime('%m/%d(') + weekdays[dt.weekday()] + dt.strftime(') %I:%M %p')
    return form_time_str

# file_type:
# 'r': reservation, 'd': dosu, 'h': hyal, 'b': blood, 'k': block
def create_xlsx(df, dir_name, file_type):
    curr_time = datetime.datetime.now()
    out_name = curr_time.strftime('%Y_%m_%d') + '_' + file_type + '.xlsx'
    out_path = os.path.join(dir_name, out_name)
    df.to_excel(out_path, sheet_name="Sheet1", header=False, index=False)

def read_rsrv_file(file_path):
    try:
        wb = pd.read_excel(file_path, sheet_name="예약환자목록")
        wb.loc[:, '일시'] = wb.loc[:, '예약일시'].map(conv_datetime)
        wb_df = wb.loc[:, ['성명', '핸드폰번호', '일시', '메모']]
        print(wb_df)
        return wb_df
    except FileNotFoundError:
        print(f"Sorry, the file {file_path} does not exist.")
        return False
    except PermissionError:
        print(f"Close the file {file_path} first.")
        return False



if __name__ == '__main__':
    dir_name = "C:/Users/lambk/OneDrive/문서/뿌리오"
    default_input_file = "reserv.xlsx"
    # dir_name = "./"
    # default_input_file = "Book1.xlsx"
    # default_input_file = "통합 문서1.xlsx"

    while True:
        rsrv_file = input(f"\n입력파일명 (Press Enter for {default_input_file},   'q' to quit): ")
        if rsrv_file == 'q':
            break
        elif rsrv_file == '':
            rsrv_file = default_input_file
        else:
            pass

        file_path = os.path.join(dir_name, rsrv_file)
        wb_df = read_rsrv_file(file_path)
        if wb_df is not False:
            # classify
            wb_df.loc[:, 'type'] = wb_df['메모'].str.lstrip().str[:2]
            grouped = wb_df.groupby('type')
            for name, group in grouped:
                create_xlsx(group.iloc[:, :-1], dir_name, name)

