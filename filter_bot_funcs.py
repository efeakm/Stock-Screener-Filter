# -*- coding: utf-8 -*-
"""
3) Progress bar UI

"""

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader as pdr




### STAT FUNCTIONS
#===================================================================================
#Get data
def get_data(ticker, lookback):
    
    stop = (pd.Timestamp.today() + pd.offsets.BusinessDay(2)).strftime("%Y-%m-%d")
    start = (pd.Timestamp.today() - pd.offsets.BusinessDay(lookback + 5)).strftime("%Y-%m-%d")
    
    
    tick = yf.Ticker(ticker)
    ret = tick.history(period = '1d', start = start, end = stop).tail(lookback)
    return ret



#calculates stock performance from Open to Open
def calculate_performance(df, period):
    df_temp = df.tail(period).copy()
    return (df_temp['Open'].iloc[-1] - df_temp['Open'].iloc[0]) / df_temp['Open'].iloc[0] * 100



#Calculates last year's performance for a given ticker
def calculate_yearly_performance(ticker):
     
    stop = pd.Timestamp.today().date().strftime("%Y-%m-%d")
    start = (pd.Timestamp.today() - pd.DateOffset(years = 1)).strftime("%Y-%m-%d")
    
    tick = yf.Ticker(ticker)
    df_year = tick.history(period = '1d', start = start, end = stop)
    
 
    return (df_year['Open'].iloc[-1] - df_year['Open'].iloc[0]) / df_year['Open'].iloc[0] * 100



#Filters stock by checking if the last Open price is within a price range
def stockprice_filter(df, top_limit, bottom_limit):
    return (df['Open'].iloc[-1] <= top_limit) and (df['Open'].iloc[-1] >= bottom_limit)



#Checks whether the lowest low in performance period is within given day threshold i.e. abs_low_lookback
def abs_low_filter(df, abs_low_lookback, performance_period):  
    
    df_temp = df.tail(performance_period).copy()
    low_to_today_day_diff = (len(df_temp) - 1 - df_temp['Low'].argmin())
    
    return low_to_today_day_diff <= abs_low_lookback



#Checks whether the highest high in performance period is within given day threshold i.e. abs_low_lookback
def abs_high_filter(df, abs_high_lookback, performance_period):
    df_temp = df.tail(performance_period).copy()
    high_to_today_day_diff = (len(df_temp) - 1 - df_temp['High'].argmax())
    
    return high_to_today_day_diff <= abs_high_lookback



# Calculates avg volume for last x days
def avg_volume(df, period):
    return df['Volume'].tail(period).mean()



#Checks whether avg volume is above min_threshold
def avg_volume_filter(df, period, min_threshold):
    return avg_volume(df, period) >= min_threshold



#Gets market caps of ticker_list
def market_cap(ticker):
    return float(pdr.data.get_quote_yahoo(ticker)['marketCap'].values)


#Filters stocks below market_cap_threshold
def market_cap_filter(cap_value, market_cap_threshold):
    return cap_value >= market_cap_threshold



### MTP FUNCTIONS
#=========================================================================

#Calculates Most Touched Point i.e. Price Profile
def mtp(df, period, num_hbar = 10):
    
    df_mtp = df[-(period+1):-1].copy()
    
    #calculate hbar width
    rangee = df_mtp['High'].max() - df_mtp['Low'].min()
    hbar_width = rangee/num_hbar
    
    lowest_low = df_mtp['Low'].min()
    
    #Get bottom and top levels
    top_lines = []
    bottom_lines = []
    for i in range(num_hbar):
        top_lines.append( lowest_low + (i+1) * hbar_width )
        bottom_lines.append( lowest_low + i * hbar_width )
    
    #Get number of candles between levels
    num_candles = [0] * num_hbar
    for i in range(num_hbar):
        for j,row in df_mtp.iterrows():
            candle_below = row['High'] < bottom_lines[i]
            candle_above = row['Low'] > top_lines[i]
            candle_isin = not (candle_below or candle_above)
            if candle_isin:
                num_candles[i] += 1
    
    #Create output dataframe
    ret = pd.DataFrame(bottom_lines, columns = ['bottom'])
    ret['top'] = top_lines
    ret['num_candles'] = num_candles

    return ret


#Checks whether the max candle number in mtp is above given threshold
def mtp_min_candles_filter(df_mtp, threshold):
    return df_mtp['num_candles'].max() >= threshold



# Gets the peak mtp area closest to current open price
def get_mtp_area(df, df_mtp):
    
    mask = df_mtp['num_candles'] == df_mtp['num_candles'].max()
    df_masked = df_mtp[mask].copy()
    
    
    #Divide areas if they are not consecutive
    list_of_df = np.split(df_masked, np.flatnonzero(np.diff(df_masked.index) != 1) + 1)
    
    
    #Calculate distance from current open price to midpoint of the area
    distances_from_open = []
    for dataframe in list_of_df:
        mean_price_of_area = np.mean([dataframe['bottom'].mean(), dataframe['top'].mean()])
        distances_from_open.append( np.abs(df['Open'].iloc[-1] - mean_price_of_area) )
    
    
    #Find and return the area with the minimum distance to current open price
    closest_area_index = np.argmin(distances_from_open)
    
    return list_of_df[closest_area_index]


# Checks whether peak area of mtp/price is less than max threshold
def mtp_range_filter(df_mtp, df_area, threshold_percent):
    
    peak_area = df_area['top'].max() - df_area['bottom'].min()
    return peak_area / df_area['bottom'].min() <= threshold_percent/100


# Get status of the stock according to open, close and mtp area alignments
def get_status(df, df_area):
    
    area_top = df_area['top'].max()
    area_bottom = df_area['bottom'].min()
    
    candle_open = df['Open'].iloc[-1]
    candle_close = df['Close'].iloc[-1]

    
    #Is open price above the area
    is_open_above = candle_open > area_top
    is_open_below = candle_open < area_bottom
    
    
    #Open outside mtp area
    #-----------------------------------------------------------------------------

    #Open above mtp area
    if is_open_above:
        if candle_close < area_bottom:
            return 'short'
        elif candle_close < area_top:
            return 'close in mtp'
        else:
            return 'pending'
    
    #Open below mtp area
    if is_open_below:
        if candle_close > area_top:
            return 'long'
        elif candle_close > area_bottom:
            return 'close in mtp'
        else:
            return 'pending'
        
    #Open inside mtp_area    
    #-------------------------------------------------------------------------------
    is_candle_red = candle_open > candle_close
    is_candle_green = candle_open < candle_close
    
    is_open_inside_mtp_area = candle_open >= area_bottom and candle_open <= area_top
    
    if is_open_inside_mtp_area and is_candle_red:
        if candle_close < area_bottom:
            return 'short'
        elif candle_close < area_top:
            return 'close in mtp'
        else:
            return 'pending'
        
    if is_open_inside_mtp_area and is_candle_green:
        if candle_close > area_top:
            return 'long'
        elif candle_close > area_bottom:
            return 'close in mtp'
        else:
            return 'pending'
        

    return





### RESULT FUNCTIONS
#=====================================================================================

# Gets a row of result for a ticker
def get_ticker_result(ticker, performance_lookback, price_top_limit, price_bottom_limit,
                      abs_low_point_window, abs_high_point_window,
                      avg_vol_window, avg_vol_min, market_cap_threshold,
                      mtp_lookback, mtp_num_hbars, min_candles_for_mtp,
                      mtp_range_perc):
    
    
    lookback = max(performance_lookback, mtp_lookback) 
    df = get_data(ticker, lookback)
    
    # Stop if there is no data
    if len(df) == 0:
        return ticker
    
    # Stock price filter
    if not stockprice_filter(df, price_top_limit, price_bottom_limit):
        return
    
    
    #Abs low filter
    if not abs_low_filter(df, abs_low_point_window, performance_lookback):
        return
    
    
    #Abs high filter
    if not abs_high_filter(df, abs_high_point_window, performance_lookback):
        return
    
    
    #Avg vol filter
    if not avg_volume_filter(df, avg_vol_window, avg_vol_min):
        return
    
    
    #Calculate mtp
    df_mtp = mtp(df, mtp_lookback, num_hbar = mtp_num_hbars)
    
    # Min no of candles for mtp filter
    if not mtp_min_candles_filter(df_mtp, min_candles_for_mtp):
        return
        
    #Get mtp area
    df_area = get_mtp_area(df, df_mtp)
    
    # Max MTP area filter
    if not mtp_range_filter(df_mtp, df_area, mtp_range_perc):
        return
    
    
    #Get market cap and filter out
    market_cap_value = market_cap(ticker)
    if not market_cap_filter(market_cap_value, market_cap_threshold):
        return
    
    
    # If the ticker has passed all the filters add relevant info
    #-------------------------------------------------------------------------------
    # Create ticker row for result dataframe
    ticker_row_info = []
    
    #Add ticker name to result dataframe
    ticker_row_info.append(ticker)
    
    
    #Add lookback period and yearly performance to the result dataframe
    ticker_row_info.append(calculate_performance(df, performance_lookback))
    ticker_row_info.append(calculate_yearly_performance(ticker))
    
    
    #Add market value info to the result dataframe
    ticker_row_info.append(market_cap_value)
    
    
    #Add avg volume to the result dataframe
    ticker_row_info.append( avg_volume(df, avg_vol_window) )
    
    #Add number of candles in peak MTP area to the result dataframe
    ticker_row_info.append(df_area['num_candles'].max())
    
    #Add top and bottom levels of peak MTP area to the result dataframe
    ticker_row_info.append(df_area['top'].max())
    ticker_row_info.append(df_area['bottom'].min())
    

    
    #Add status info to the result dataframe
    ticker_row_info.append(get_status(df, df_area))
    
    return ticker_row_info











