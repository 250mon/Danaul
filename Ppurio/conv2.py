import pandas as pd
import os
import datetime


def conv_datetime(dt):
    weekdays = ('월', '화', '수', '목', '금', '토', '일')
    # dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    form_time_str = dt.strftime('%m/%d(') + weekdays[dt.weekday()] + dt.strftime(') %I:%M %p')
    return form_time_str

def make_out_file_name(flag):
    curr_time = datetime.datetime.now()
    out_name = curr_time.strftime('%m%d') + flag + '.xlsx'
    return out_name

# flag: None(False) or "bad"(True)
def create_xlsx(df, dir_name, flag=''):
    if df is None:
        return
    out_name = make_out_file_name(flag)
    out_path = os.path.join(dir_name, out_name)

    if flag:
        df.to_excel(out_path, sheet_name="Sheet1", header=True, index=False)
    else:
        df.to_excel(out_path, sheet_name="Sheet1", header=False, index=False)



def read_rsrv_file(file_path):
    try:
        wb = pd.read_excel(file_path)
        if '일시' not in wb.columns:
            wb.loc[:, '일시'] = wb.loc[:, '예약일시'].map(conv_datetime)
        wb_df = wb.loc[:, ['성명', '핸드폰번호', '일시', '메모']]
        print(wb_df)
        return wb_df
    except FileNotFoundError:
        print(f"{file_path} 파일이 존재하지 않습니다.")
        return False
    except PermissionError:
        print(f"{file_path} 파일이 열려 있습니다. 파일을 닫고 다시 시도 해주세요.")
        return False
    except KeyError:
        print(f"{file_path} 파일이 형식에 맞지 않습니다.")
        return False

def check_df(wb_df):
    pattern = r"예약|연골|검사|도수|주사|비디"
    contents = {"예약": "치료경과",
                "연골": "무릎연골주사",
                "검사": "검사결과",
                "도수": "도수치료",
                "주사": "주사치료",
                "비디": "비타민D주사"}
    wb_df.loc[:, 'Check'] = wb_df.loc[:, '메세지코드'].str.fullmatch(pattern)

    group_obj = wb_df.groupby('Check')
    good_df = None
    bad_df = None
    if True in group_obj.groups.keys():
        # For preventing a view being assigned value, we need a copy a good_df
        good_df = group_obj.get_group(True).copy()
        good_df.loc[:, '메세지'] = good_df.loc[:, '메세지코드'].map(contents)
    if False in group_obj.groups.keys():
        bad_df = wb_df.groupby('Check').get_group(False)
    return good_df, bad_df


if __name__ == '__main__':
    # dir_name = "C:/Users/lambk/OneDrive/문서/Danaul Util Devel/뿌리오"
    # default_input_file = "reserv"
    dir_name = "./"
    # default_input_file = "Book1"
    default_input_file = "통합 문서1"

    while True:
        rsrv_file = input(f"\n입력파일명 (Press Enter for {default_input_file}.xlsx,   'q' to quit): ")
        if rsrv_file == 'q':
            break
        elif rsrv_file == '':
            rsrv_file = default_input_file
        else:
            pass

        file_path = os.path.join(dir_name, rsrv_file + '.xlsx' if '.xlsx' not in rsrv_file else rsrv_file)
        wb_df = read_rsrv_file(file_path)
        if wb_df is not False:
            wb_df.loc[:, '메세지코드'] = wb_df['메모'].str.lstrip().str.split(";").str.get(0)
            good_df, bad_df = check_df(wb_df)
            if good_df is not None:
                print(f"\n{good_df.shape[0]}명 예약 환자 파일 작성 성공!")
                create_xlsx(good_df.loc[:, ['성명', '핸드폰번호', '일시', '메세지']], dir_name)
            if bad_df is not None:
                print(f"{bad_df.shape[0]}명 예약 환자 파일 작성 실패!")
                print(f"{file_path} 파일에서 {bad_df['성명'].to_list()} 메모 내용을 형식에 맞게 수정하세요 !!!!!!!!!!!!")
                create_xlsx(bad_df.loc[:, ['성명', '핸드폰번호', '일시', '메모']], dir_name, 'bad')
