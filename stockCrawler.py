#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 19:40:17 2020

@author: linmiepii
"""

# step1. import package 
import requests
import pandas as pd
import numpy as np
from io import StringIO
import sqlite3   
from sqlite3 import Error, DatabaseError                             
from datetime import datetime, timedelta
from datetime import date
from datetime import time
import time as t
from colorama import Fore, Style
import matplotlib.pyplot as plt
import seaborn as sns
import twstock
from tqsdk import TqApi
from talib.abstract import *
import mpl_finance as mpf

def update_daily_price():  
# 確認可否連接資料庫 
    # conn = sqlite3.connect('../data/stock_fund.db')
    conn = sqlite3.connect('../data/twstock.db')
# 進入資料庫抓取最後一天，若無資料庫，則從預設值開始
# bug:exception可以detect db裡沒有daily_price table，但else無法執行
    startDay = '20170930'
    try:
        startDay = pd.read_sql(sql = "SELECT MAX(date) FROM daily_price", con = conn, parse_dates = True).iloc[0,0]
    except Exception as e:
        print(e)
    else:
        pass   
# 建立要更新的date list
    startDay_parse = datetime.strptime(startDay, '%Y%m%d') + timedelta(days=1)     
    datelist = pd.date_range(startDay_parse,date.today()).strftime('%Y%m%d').tolist()
# 避免crawler被封鎖，使用header並降低每秒請求的數量
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}  
    for dateStr in datelist:
        try:
            r = requests.post('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + dateStr + '&type=ALL', headers = headers)
        except Exception as e:
            print('*** Warning: can not get price at' + dateStr)
            print(e)       
        
        ETF_track_list = ['00642U','0050','0056','00850','00692','00762', '00737','00646']
        
        str_list = []
      
        # return r.text
    
        for i in r.text.split('\n'):
    
            if len(i.split('",')) == 17 and i[0] != '=':       
                i = i.strip(",\r\n")
                str_list.append(i)  
            
            if len(i.split('",')) == 17 and i[1] == '證':       
                i = i.strip(",\r\n")
                str_list.append(i) 
            
            if len(i.split('",')) == 17 and i.split('","')[0].strip('="') in ETF_track_list:

                i = i.strip(",=\r\n")
                str_list.append(i)
                
  
                
                
        if str_list:
            df = pd.read_csv(StringIO("\n".join(str_list)))  
            df['date'] = dateStr             
            df.to_sql('daily_price', conn, if_exists='append', index=False) 
            print(dateStr + " data is sent into sql")
        else:
            print(dateStr + " no data today")    
        t.sleep(5)
    print(f'Update daily_price done. from {Fore.GREEN}{startDay}{Style.RESET_ALL} to today')
    
    
    
def update_trading():
    # 確認可否連接資料庫 
    # conn = sqlite3.connect('../data/stock_fund.db')
    conn = sqlite3.connect('../data/twtrading.db')
# 進入資料庫抓取最後一天，若無資料庫，則從預設值開始
# bug:exception可以detect db裡沒有daily_price table，但else無法執行
    startDay = '20180930'
    try:
        # pass
        startDay = pd.read_sql(sql = "SELECT MAX(date) FROM daily_trade", con = conn, parse_dates = True).iloc[0,0]
    except Exception as e:
        print(e)
    else:
        pass   
# 建立要更新的date list
    startDay_parse = datetime.strptime(startDay, '%Y%m%d') + timedelta(days=1)     
    datelist = pd.date_range(startDay_parse,date.today()).strftime('%Y%m%d').tolist()
# 避免crawler被封鎖，使用header並降低每秒請求的數量
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}  
    for dateStr in datelist:
        
        try:
            r = requests.post('http://www.tse.com.tw/fund/T86?response=csv&date='+dateStr+'&selectType=ALLBUT0999', headers = headers)
        except Exception as e:
            print('*** Warning: can not get price at' + dateStr)
            print(e) 
        
        
        
        
        if r.text:
            df = pd.read_csv(StringIO(r.text), header=1).dropna(how='all', axis=1).dropna(how='any')
            df['date'] = dateStr
            df['證券代號'] =   df['證券代號'].apply(lambda x: x.strip('="'))    
            df.to_sql('daily_trade', conn, if_exists='append', index=False) 
            print(dateStr + " data is sent into sql")
        else:
            print(dateStr + " no data today")    
        t.sleep(5)
    print(f'Update daily_trading done. from {Fore.GREEN}{startDay}{Style.RESET_ALL} to today')
    
    
    
def price_get(stock_id='2317', endDay=datetime.today().strftime('%Y%m%d') , duration = 100):
    '''

    Parameters
    ----------
    stock_id : string, optional
        DESCRIPTION. The default is '2317'.
    endDay : string, format %Y%m%d  optional
        DESCRIPTION. The default is datetime.today().strftime('%Y%m%d').
    duration : int, optional
        DESCRIPTION. The default is 100.

    Returns
    -------
    get_data : TYPE
        DESCRIPTION.

    '''
    conn = sqlite3.connect('../data/stock_.db')  
    cursor = conn.cursor()
    endDay_parse = datetime.strptime(endDay, '%Y%m%d')
    startDay_parse = endDay_parse - timedelta(days = duration)
    startDay = startDay_parse.strftime('%Y%m%d')
     
    try:
        # get_data = pd.read_sql(sql = "SELECT date,收盤價 FROM daily_price WHERE 證券代號 = 6196 AND date BETWEEN ? AND ?", con = conn)
        cursor.execute("SELECT date,收盤價 FROM daily_price WHERE 證券代號 = ? AND date BETWEEN ? AND ?", (stock_id, startDay, endDay))
        
    except Exception as e:
        print(e)
    
    getPrice = pd.DataFrame(cursor.fetchall())
    
    getPrice.columns = ['date','收盤價']
    getPrice['收盤價'] = getPrice['收盤價'].astype(float)
    getPrice['date'] = getPrice['date'].apply(lambda x: datetime.strptime(x, '%Y%m%d'))
    conn.close()
    return getPrice
def deal_get(stock_id):
    
    conn = sqlite3.connect('../data/stock.db')    
    cursor = conn.cursor()
    try:
        # cursor.execute("SELECT date, deal_type FROM deal_table WHERE 證券代號 = ?", (stock_id))
        cursor.execute("SELECT * FROM deal_table WHERE 證券代號 = ? ",(stock_id))
        
    except Exception as e:
        print(e)
        return None
    getDeal = pd.DataFrame(cursor.fetchall()) 
    getDeal.columns = ['date', 'deal_type','證券代號','qty','price']
    conn.close()
    return getDeal
def seaborn_style():
    style = ('white','dark','whitegrid','darkgrid','ticks')
    context = ('notebook','paper','talk','poster')
    palette = ('pastel','muted','dark','bright','colorblind','dark')
    sns.set_style(style[1])
    sns.set_context(context[0])
    sns.set_palette(palette[4])
#    sns.despine(offset=10, trim=True)
    sns.despine(offset=10)
    sns.despine(bottom=True)  
def put_mark(opening, close):
    if opening != 0 and close != 0:
        if (close - opening) / opening > 0.07:
            return 0
        elif (close - opening) / opening < -0.07:
            return 1   
        
def evaluation(data, stock_id , timming, how_long):
    for ts in timming:
        te = ts + timedelta(how_long)
        
        for id in stock_id:
            use_data = data[data.證券代號 == id]
            use_data = use_data[use_data.date>ts][use_data.date<te]      
            # sns.lineplot(x='date', y='收盤價', data=use_data)
            # plt.xticks(rotation=45)
            # plt.show()
            
            use_data['ratio'] = use_data.apply(lambda x: x['成交股數']/x['成交筆數'], axis = 1)
            # sns.lineplot(x='date', y='成交股數', data=use_data)
            sns.lineplot(x='date', y='ratio', data=use_data)
            plt.xticks(rotation=45)
            plt.show()

def find_anomalies(random_data):
    # Set upper and lower limit to 3 standard deviation
    random_data_std = np.std(random_data)
    random_data_mean = np.mean(random_data)
    anomaly_cut_off = random_data_std * 2.66
    
    lower_limit  = random_data_mean - anomaly_cut_off 
    upper_limit = random_data_mean + anomaly_cut_off
    # print(lower_limit)
    anomalies_l = []
    anomalies_u = []
    for outlier in random_data:
        if outlier < lower_limit:
            anomalies_l.append(outlier)
        elif outlier > upper_limit:
            anomalies_u.append(outlier)
            
    # if anomalies_l:
    #     lv = max(anomalies_l)
    # else:
    #     lv = None
    # if anomalies_u:
    #     uv = min(anomalies_u)
    # else:
    #     uv = None      
    # return (lv, uv)
    return(lower_limit , upper_limit)


def RSI_dir_check(short, long):
    if short > long:
        return 1
    elif short < long:
        return -1
    elif short == long:
        return 0



if __name__ == '__main__':
    update_trading()
    update_daily_price()
    
    # seaborn_style()
    # query_stock_id = '2317'
    # getDeal = deal_get(query_stock_id)
    # getPrice = price_get(query_stock_id, duration = 100)
    # ax = sns.lineplot(x='date', y='收盤價' , data = getPrice)
    
    # if getDeal != None:
    #     print('not none')
    #     getDeal[['qty','price']] = getDeal[['qty','price']].astype(float)
    #     date_array = getDeal.values
    #     for dealData in date_array:
    #         if dealData[1] == 'sell':
    #             plt.axvline(dealData[0],0, dealData[3]*0.1, linewidth = 1, color = 'r') 
                
    #         elif dealData[1] == 'buy':
    #             plt.axvline(dealData[0],0,dealData[4],linewidth = 1, color = 'g') 
    #             pass
            
   
    # plt.title(f'** {query_stock_id} ** daily price')
    # plt.ylabel('price')
    # plt.xticks(rotation = 36)
  
    conn = sqlite3.connect('../data/twstock.db')  
    # conn = sqlite3.connect('../data/stock.db')  
    stock = pd.read_sql(sql = 'SELECT * FROM daily_price', con = conn)
    stock = stock[['成交股數','成交筆數','成交金額','開盤價','最高價', '最低價', '收盤價','漲跌價差', 'date','證券代號']]
    stock.columns = ['capacity','transaction','turnover','open','high','low','close','change','date','id']
    stock['date'] = stock['date'].apply(lambda x: datetime.strptime(x,'%Y%m%d').date())
    stock = stock[stock['capacity'] != '0']
    for i in range(7):
        stock.iloc[:,i] = stock.iloc[:,i].apply(lambda x: x.replace(',',''))
        stock.iloc[:,i] = stock.iloc[:,i].apply(lambda x: x.replace('--','0'))
        
    stock[['open','high', 'low', 'close' ,'turnover','capacity','transaction']] = stock[['open','high', 'low', 'close' ,'turnover','capacity','transaction']].astype(float)
 
    # # id_focus = ['2317','2377','2352','6202','4919','3661','2330','4977','2353','6411','4968','8183','2448','8069']
    # id_focus = ['00642U','0050','0056','00850','00692','00762', '00737','00646']
    
    
    # 5G 
    # id_focus = ['3419','6213','2314','2455','3450','4977']
    
    # 散熱
    
    
    # IC設計
    # id_focus = ['6202','4919','2454','4968','3443']
    # PCB載板
    
    
    # 記憶體
    id_focus = ['2337','2344']
    
    # 廢棄物
    
    
    
    for sid in id_focus:
        df = stock[stock['id'] == sid]
        df.set_index('date', inplace = True)
        df = df.tail(200)
               
        sma_5 = SMA(df,5, price='close')
        sma_10 = SMA(df,10, price='close')
        sma_30 = SMA(df,30, price='close')
        sma_df = pd.concat([sma_5,sma_10,sma_30])
        # uses close prices (default)
        # upper, middle, lower = BBANDS(df, 20, 2, 2)
        
        # uses high, low, close (default)
        slowk, slowd = STOCH(df, 5, 3, 0, 3, 0) # uses high, low, close by default
        
        # uses high, low, open instead
        # slowk, slowd = STOCH(df, 5, 3, 0, 3, 0, prices=['high', 'low', 'open'])
        
        
        # #創建圖框
        fig = plt.figure(figsize=(24, 16))
        ax = fig.add_subplot(1, 1, 1)
        # #設定座標數量及所呈現文字
        # ax.set_xticks(range(0, len(df.index), 10))
        # ax.set_xticklabels(df.index[::10],rotation=60)
        # #使用mpl_finance套件candlestick2_ochl
        # mpf.candlestick2_ochl(ax, df['open'], df['close'], df['high'],
        #       df['low'], width=0.6, colorup='r', colordown='g', alpha=0.75);
        
        # ax1 = plt.figure(figsize=(24,8))
        # ax = fig.add_subplot(3, 1, 2)
        # ax.plot(sma_df)
        

    
        
        # kds線
        KD_df = STOCH(df,fastk_period=9, slowk_period=3,slowd_period=3)
        # STOCH(df,fastk_period=9, slowk_period=3,slowd_period=3).tail(50).plot(figsize=(16,8))
        # ax.plot(KD_df.tail(50))
        
        # MACD線
        MACD_df = MACD(df,fastperiod=6, slowperiod=12, signalperiod=9).tail(6)  
        # ax.plot(MACD_df[['macd', 'macdsignal']])
        # plt.xticks(range(len(MACD_df.index)), MACD_df.index)
        # ax.bar(x = MACD_df.index, height = MACD_df['macdhist'],width=1, bottom=None, align='center',color = 'green')
        
        # bar(x, height, , **kwargs)[source]
        
        
        # RSI線
        
        RSI_f = RSI(df, timeperiod = 5)
        RSI_s = RSI(df, timeperiod  = 10)
        RSI_df = pd.concat([RSI_f , RSI_s], axis = 1)
        RSI_df.columns  = ['RSI_f', 'RSI_s']
        plt.plot(RSI_df.tail(200), linewidth = 5)
        
       
        
        RSI_df['less than 20'] = RSI_df.apply(lambda x:'True' if (x['RSI_f']<20 and x['RSI_s']<20) else 'False', axis = 1)
        # RSI_df['less than 20'] = RSI_df.apply(lambda x:'True' if (x['RSI_f']<20 ) else 'False', axis = 1)
        RSI_df['direction'] = RSI_df.apply(lambda x: RSI_dir_check(x['RSI_f'], x['RSI_s']) , axis = 1)
        RSI_df['cond1'] = RSI_df['less than 20'].shift(1)
        RSI_df['cond2'] = RSI_df['direction'].shift(1)
        RSI_df['buying_mark'] = RSI_df.apply(lambda x: 10000 if ((x['cond2'] == -1 and x['direction'] ==1) and x['cond1'] == 'True') else 0, axis = 1)
        buy_in = RSI_df[RSI_df['buying_mark'] == 10000].index
        
        
        for i in buy_in:
            plt.axvline(x=i, ymin=0, ymax=500, linewidth = 8, color = 'green')
        plt.show()
        
        
        plt.plot(df['capacity'])
        for i in buy_in:
            plt.axvline(x=i, ymin=0, ymax=500, linewidth = 4, color = 'green')
        plt.show()
        
        # RSI(df).tail(50).plot(figsize=(16,8))
        # df['close'].tail(50).plot(figsize=(16,8), secondary_y = True)
        
    
        # uses close prices (default)
        # output = SMA(df, timeperiod=25)
        
        # uses open prices
        output = SMA(df, timeperiod=25, price='close')
        

    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # # id_focus = process_data['id'].unique()
    # for stock_id in id_focus:
    #     analysis_data = process_data[process_data['id']== stock_id]
    #     analysis_data = analysis_data.sort_values(by = ['date'], ascending=False)
    #     analysis_data.reset_index(inplace = True, drop = True)
    #     sin_outlier = []    
        
    #     date_focus = analysis_data['date']
    #     for on_day in date_focus:
    #         i = analysis_data[analysis_data['date'] == on_day].index[0]
            
    #         if i <=900:
            
    #             if i == 0:
    #                 input_data = analysis_data['close'].iloc[-150:]
    #                 LV , UV = find_anomalies(input_data)
    #                 current_value = analysis_data[analysis_data['date'] == on_day]['close'][0]
    #                 if LV and current_value <= LV:
    #                     print(stock_id +': current value' + str(current_value) + 'is lower than outlier' + str(LV))
            
    #             else:
    #                 input_data = analysis_data['close'].iloc[-150-i:-i]
    #                 LV , UV = find_anomalies(input_data)
                
                
                
    #             sin_outlier.append([on_day,LV,UV])
        
        
    #     if sin_outlier:
    #         df_range = pd.DataFrame(sin_outlier) 
    #         df_range.columns = ['date', 'LV', 'UV']
    #         sns.lineplot(x='date', y='LV', data = df_range)
    #         sns.lineplot(x='date', y='UV', data = df_range)
    #         sns.lineplot(x='date', y='close', data = analysis_data)
    #         plt.title(stock_id)
    #         plt.show()
            
    #     con_outlier = []   
    #     con_outlier.append(sin_outlier)
        
    # df_outlier = pd.DataFrame(con_outlier)
    
 
    # # process_data['mark'] = process_data.apply(lambda x: put_mark(x['開盤價'], x['收盤價']), axis = 1)

    # # result = process_data.groupby('date')['mark'].sum().to_frame()
    # # happen_date = result.index[result.mark > 50]
    
    # # evaluation(process_data, ['2352'], happen_date, 100)

    # # result = result.reset_index()
    # # ax = sns.lineplot(x = 'date', y='mark', data = result )
    
    

        
    
    

     

 

    



