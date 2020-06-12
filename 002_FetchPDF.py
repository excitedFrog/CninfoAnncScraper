# Python 3.7

import os
import requests
import pandas as pd
import multiprocessing as mp

directory_df = pd.read_csv('directory20162020.csv')
save_dir = './pdf20162020/'


def worker(entry):
    uid, stock_id, stock_name, title, annc_date, query_date, query_page, dl_flag, url = entry
    annc_id = list(filter(lambda x: x.startswith('announcementId'), url.replace('?', '&').split('&')))[0].split('=')[1]
    true_url = 'http://static.cninfo.com.cn/finalpage/%s/%s.PDF' % (query_date, annc_id)
    response = requests.get(true_url)
    with open(os.path.join(save_dir, '%s.%s.%s.pdf' % (uid, query_date, annc_id)), 'wb') as fout:
        fout.write(response.content)
    return uid, stock_id, stock_name, title, annc_date, query_date, query_page, dl_flag, url, annc_id


with mp.Pool(16) as pool:
    results = pool.map(worker, directory_df.values)

directory_df_out = pd.DataFrame(data=results, columns=["uid", "stock_id", "stock_name", "title", "time", "query_date",
                                                       "query_page", "dl_flag", "url", "annc_id"])
directory_df_out.to_csv('directory20162020_out.csv')
