# Python 3.7

import sys
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import date, timedelta
from webdriver_manager.chrome import ChromeDriverManager

t0 = time.time()

year = int(sys.argv[1])
# year = 2016
start_date = date(year, 3, 2)
end_date = date(year, 12, 31)
delta = end_date - start_date
uid = 0
driver = webdriver.PhantomJS()
# driver = webdriver.Chrome(ChromeDriverManager().install())
for i in range(delta.days + 1):
    date = str(start_date + timedelta(days=i))
    print(date)
    driver.get(
        'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&startDate=%s&endDate=%s'
        % (date, date))
    _url = str()
    # go through each page of the url
    while True:
        time.sleep(1)

        # wait load completion loop
        sleep_count = 0
        while True:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            try:
                max_page = soup.find_all('li', {"class": "number"})[-1].text
                current_page = soup.find('li', {"class": "number active"}).text
            except (AttributeError, IndexError) as Error:  # this means there is no content, so break
                break
            table = soup.find('tbody')
            first_row = table.find('tr').find_all('td')
            url = first_row[2].find('a')['href']
            if url == _url:
                time.sleep(1)
                continue
            else:
                break

        # read page content
        soup = BeautifulSoup(driver.page_source, 'lxml')
        try:
            max_page = soup.find_all('li', {"class": "number"})[-1].text
            current_page = soup.find('li', {"class": "number active"}).text
        except (AttributeError, IndexError) as Error:  # this means there is no content, so break
            break

        print('Scraping %s Page %s' % (date, current_page))

        table = soup.find('tbody')
        data = list()
        for i_row, row in enumerate(table.find_all('tr')):
            uid += 1
            columns = row.find_all('td')
            stock_id = columns[0].text
            stock_name = columns[1].text.strip()
            anc_title = columns[2].text
            anc_time = columns[3].text
            url = columns[2].find('a')['href']

            if i_row == 0:
                _url = url

            data.append([uid, stock_id, stock_name, anc_title, anc_time, date, current_page, 0, url])
        df_out = pd.DataFrame(data=data, columns=["uid", "stock_id", "stock_name", "title", "time",
                                                  "query_date", "query_page", "dl_flag", "url"])
        df_out.to_csv('announcement_directory_%s.csv' % year, header=False, mode='a', index=False)

        if current_page == max_page:
            break

        button_next = driver.find_element_by_xpath('//button[@class=\'btn-next\']')
        button_next.click()

t1 = time.time()
print('Total time used: %s seconds.' % (t1-t0))
driver.quit()
