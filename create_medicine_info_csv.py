import csv
import os
import os.path
import pprint
import time
import traceback

from selenium import webdriver

# お薬検索サイトのURL
TARGET_URL = "http://search.jsm-db.info/main2.php?uriflg=JSM"

# Seleniumで取得する要素を判定するために宣言する
ELEMENT_MEDICINE_CLASS = [
    "要指導医薬品",
    "第一類医薬品",
    "第二類医薬品",
    "指定第二類医薬品",
    "第三類医薬品",
    "指定医薬部外品",
    "その他",
]

# 医薬品分類を検索する対象を宣言する
SEARCH_MEDICINE_CLASS = [
    "要指導医薬品",
    "第一類医薬品",
    "第二類医薬品",
    "指定第二類医薬品",
    "第三類医薬品",
    "指定医薬部外品",
    "その他",
]

# 以下のリスト内の要素は検索しない
NOT_ELEMENT_VALUE = [
    "セルフメディケーション税制対象"
]

# WindownsとMacでドライバーが違うのでそれぞれ定義しておく
DRIVER_WIN = "chromedriver.exe"
DRIVER_MAC = "./chromedriver"

# 各動作間の待ち時間（秒）
INTERVAL = 2

# CSVファイルを出力するパス
CSV_PATH_WIN = 'data/medicine_info.csv'
CSV_PATH_MAC = './data/medicine_info.csv'

# 出力するCSVのヘッダー
CSV_HEADER = [
    "製品名",
    "剤型",
    "メーカー名",
    "薬効分類",
    "医薬品分類",
    "効能・効果",
    "リンク"
]

# 検索結果数のXPATH
SEARCH_RESULT_COUNT_XPATH = "//html/body/center/table[3]/tbody/tr[1]/td[2]/b"

# 検索結果一覧画面から要素を取得するXPATHのテンプレート
TEMPLATE_XPATH = "//html/body/center/div/table/tbody/tr[{}]/td[{}]"

# 次のページへボタンのXPATH
NEXT_PAGE_XPATH = "//html/body/center/table[3]/tbody/tr[2]/td[3]/span/a"

# 効能・効果のXPATH
EFFICACY_EFFECT_XPATH = "//html/body/center/table[6]/tbody/tr[3]/td/table/tbody/tr/td/font"


def main():
    """
    お薬検索サイトで一般薬を検索する
    :return: 検索結果をCSVファイルに出力する
    """

    if os.name == "nt":
        driver_path = DRIVER_WIN
        output_csv_path = CSV_PATH_WIN
    else:
        output_csv_path = CSV_PATH_MAC

    # ブラウザ起動
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.maximize_window()

    time.sleep(INTERVAL)

    try:
        # 対象サイトへアクセス
        driver.get(TARGET_URL)

        time.sleep(INTERVAL)

        # 要素の取得
        element_list = driver.find_elements_by_class_name("jp2l")

        for element in element_list:
            # elementからvalueとcheckboxを抽出
            element_input = element.find_element_by_tag_name("input")
            element_value = element_input.get_attribute("value")

            # セルフメディケーション税制対象は処理しない
            if element_value in NOT_ELEMENT_VALUE:
                break

            # 検索対象の要素にはチェックを入れる
            # 検索対象以外の要素はチェックを外す
            if element_value in SEARCH_MEDICINE_CLASS:
                if not element_input.is_selected():
                    element_input.click()
            else:
                if element_input.is_selected():
                    element_input.click()

        # 検索ボタンクリック
        driver.find_element_by_id("Image5").click()

        time.sleep(INTERVAL)

        # 検索結果をCSVファイルに出力する
        with open(output_csv_path, 'w') as f:
            writer = csv.writer(f)
            # CSVのヘッダーを出力
            writer.writerow(CSV_HEADER)

            # 検索結果からお薬情報を取得する
            # 検索結果数
            text_search_result_count = driver.find_element_by_xpath(SEARCH_RESULT_COUNT_XPATH).text

            displaying_count = int(text_search_result_count[-3:].replace(" ", "").replace("件", ""))

            # 次のページの存在フラグ
            is_exist_next_page = True

            while is_exist_next_page:

                for i in range(displaying_count):
                    # 取得要素の位置番号
                    tr_number = (i * 3) + 2
                    # 製品名
                    product_name = driver.find_element_by_xpath(TEMPLATE_XPATH.format(tr_number, 2)).text
                    # 剤型
                    agent_type = driver.find_element_by_xpath(TEMPLATE_XPATH.format(tr_number, 3)).text
                    # メーカー名
                    maker_name = driver.find_element_by_xpath(TEMPLATE_XPATH.format(tr_number, 4)).text
                    # 薬効分類
                    medicinal_effect_classification = driver.find_element_by_xpath(
                        TEMPLATE_XPATH.format(tr_number, 5)).text
                    # 医薬品分類
                    medicine_product_classification = driver.find_element_by_xpath(
                        TEMPLATE_XPATH.format(tr_number, 6)).text

                    # リンク先を新規タブで表示する
                    target_xpath = TEMPLATE_XPATH.format(tr_number, 2) + "/a"
                    driver.find_element_by_xpath(target_xpath).click()

                    # 詳細タブに移動
                    driver.switch_to.window(driver.window_handles[-1])

                    # 効能・効果
                    efficacy_effect = driver.find_element_by_xpath(EFFICACY_EFFECT_XPATH).text

                    # CSVに出力するデータ
                    # TODO アマゾンの商品ページのリンクを取得する
                    row = [
                        product_name,
                        agent_type,
                        maker_name,
                        medicinal_effect_classification,
                        medicine_product_classification,
                        efficacy_effect,
                        ""
                    ]

                    # CSVに出力する
                    writer.writerow(row)

                    # 検索結果タブに戻る
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(INTERVAL)

                # 次のページがあるか判定
                next_page = driver.find_elements_by_xpath(NEXT_PAGE_XPATH)
                if len(next_page) > 0:
                    # あれば次のページへ遷移
                    next_page[0].click()
                else:
                    # なければwhileから抜ける
                    is_exist_next_page = False

    except:
        traceback.print_exc()
    finally:
        # ブラウザを閉じる
        driver.quit()


if __name__ == "__main__":
    main()
