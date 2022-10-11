# -*- coding: utf-8 -*-
"""
- Remove 10 ticker limit
"""


import streamlit as st
import pandas as pd
from filter_bot_funcs import get_ticker_result
from stqdm import stqdm
import time


### INPUT PARAMETERS
#=======================================================================================


#Ticker list
#------------------------------------------------------------------------------
TICKER_LIST = pd.read_csv('ticker_list.csv', header = None).iloc[:,0]
TICKER_LIST = TICKER_LIST.fillna("")


#Stat Parameters
#-------------------------------------------------------------------------------
st.title('Input Parameters')


st.subheader('Statistics Parameters')
performance_lookback_help = '''If a number is entered for the option, Excel calculates the performance since the specified days. It is 
important to note here that only trading days are taken into account.
If you enter the number 5 in the field on 09/10/2022, the performance period is from 09/05/2022 to 
09/09/2022. The performance is given in %.'''
PERFORMANCE_LOOKBACK = st.number_input('Performance Lookback Period', min_value = 3, step = 1, value = 21, help = performance_lookback_help)


PRICE_TOP_LIMIT = st.number_input('Maximum Price Filter', min_value = 0.0, step = 0.01, format = "%f", value = 10000.00, help = "Maximum stock price to be included in the results")
PRICE_BOTTOM_LIMIT = st.number_input('Minimum Price Filter', min_value = 0.0, step = 0.01, format = "%f", value = 0.00, help = "Minimum stock price to be included in the results")


abs_point_help = '''If a parameter is specified here, the stock must have reached an absolute high or low within the time 
period. To better explain the function, here is an example:
For Absolute Low Point, the number 21 is entered.
All stocks that do not have an absolute low point within 21 trading days are sorted out. Stocks that 
have a low point within 21 are displayed. The same applies to Absolute High Point.'''
ABS_LOW_POINT_WINDOW = st.number_input('Absolute Low Point Period', min_value = 1, step = 1, value = 21, help = abs_point_help)
ABS_HIGH_POINT_WINDOW = st.number_input('Absolute High Point Period', min_value = 1, step = 1, value = 21, help = abs_point_help)


avg_vol_help = ''' If a number is specified, a corresponding number of data sets is taken into account in the calculation.'''
AVG_VOL_WINDOW = st.number_input('Average Volume Period', min_value = 1, step = 1, value = 10, help = avg_vol_help)
AVG_VOL_MIN = st.number_input('Minimum Average Volume Filter', min_value = 0.0, value = 100.00, help = 'Here you can specify a value that determines how much average volume a share must have at least. If a share has less average volume, it will not be displayed.')

MARKET_CAP_MIN = st.number_input('Minimum Market Cap', min_value = 0, value = 0, step = 1000, help = "Filters stocks with market cap lower than this threshold")

NUMBER_OF_TICKERS = st.number_input('Number of Tickers to Search', min_value = 10, value = len(TICKER_LIST), help = "Sets how many stocks to search")
TICKER_LIST = TICKER_LIST[:NUMBER_OF_TICKERS]


#MTP Parameters
#---------------------------------------------------------------------------------

st.subheader("")
st.subheader('MTP Parameters')


MTP_LOOKBACK = st.number_input('MTP Lookback Period', min_value = 2, step = 1, value = 10, help = "Number of business days to calculate MTP")
MTP_NUM_HBARS = st.number_input('MTP Number of Horizontal Bars', min_value = 2, max_value = 500, step = 1, value = 10, help = 'Number of Horizontal Bars in MTP Calculation')
MIN_CANDLES_FOR_MTP = st.number_input('MTP Minimum Candles Filter', min_value = 0, step = 1, value = 5, help = 'Here you can define the minimum number of candles the MTP must consist of.')
MTP_RANGE_PERC = st.number_input('MTP Maximum Range Percentage Filter', min_value = 0.0, step = 0.00001, format = "%f", value = 10.00, help = 'Specifies the maximum size of the MTP range. Stocks with MTP ranges that exceed the specified parameter are not displayed.')
    
    



### EXCEPTION HANDLING
#=========================================================================================






### GET RESULTS
#=================================================================================================

# Result Functions
#--------------------------------------------------------------------------------------

# Iterates over ticker_list to get all results and also returns non found tickers
def get_all_results(ticker_list, performance_lookback, price_top_limit, price_bottom_limit,
                      abs_low_point_window, abs_high_point_window,
                      avg_vol_window, avg_vol_min, market_cap_min,
                      mtp_lookback, mtp_num_hbars, min_candles_for_mtp,
                      mtp_range_perc):
    start = time.time()
    
    
    results = []
    not_founds = []
    for i in stqdm(range(len(ticker_list))):
        
        ticker = ticker_list[i]
        
        if i%20 == 0:
            print(i,time.time()-start)
        
        try:
            ticker_result = get_ticker_result(ticker, performance_lookback, price_top_limit, price_bottom_limit,
                                            abs_low_point_window, abs_high_point_window,
                                            avg_vol_window, avg_vol_min, market_cap_min,
                                            mtp_lookback, mtp_num_hbars, min_candles_for_mtp,
                                            mtp_range_perc)
        except:
            not_founds.append(ticker)
        
        
        # Add ticker row to results
        if type(ticker_result) == list:
            results.append(ticker_result)
            
        # If ticker data is not available i.e. return is the ticker itself, add it to not_founds
        elif type(ticker_result) == str:
            not_founds.append(ticker_result)
    
    
    
    
    # Process Results
    results = pd.DataFrame(results,
                           columns = ['Ticker', 'Lookback_perf', 'Yearly_perf',
                                      'Market_Cap','Avg_Vol',
                                      'Candles_in_MTP', 'MTP_top_level', 'MTP_bottom_level',
                                      'Status'])  
        
    results['Lookback_perf'] = results['Lookback_perf'].round(3)
    results['Yearly_perf'] = results['Yearly_perf'].round(3)

    
    
    return results, not_founds



# Returns df_result and not_found tickers. Suppress param is required to
# stop sqtdm warning in the get_all_results function
@st.cache(suppress_st_warning=True)
def results():
    df_result, not_founds = get_all_results(TICKER_LIST, PERFORMANCE_LOOKBACK, PRICE_TOP_LIMIT, PRICE_BOTTOM_LIMIT,
                    ABS_LOW_POINT_WINDOW, ABS_HIGH_POINT_WINDOW,
                    AVG_VOL_WINDOW, AVG_VOL_MIN, MARKET_CAP_MIN,
                    MTP_LOOKBACK, MTP_NUM_HBARS, MIN_CANDLES_FOR_MTP, MTP_RANGE_PERC)
    return df_result, not_founds


#Converts pandas dfs to csv to make it downloadable over a button
@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')


# Page Structure
#-------------------------------------------------------------------------------------
st.header('')
st.title('Get Results')

# If checkbox is checked
if st.checkbox('Filter Stocks'):
    
    #Creates datas
    df_result, not_founds = results()
    
    
    # Filter and sort settings for the result table
    st.subheader('')
    st.subheader('Table Settings')
    num_of_rows = st.number_input("Number of Rows to Show", min_value = 1, value = 10, step = 1, max_value = max(10,len(df_result)),
                        help = "Sets number of rows in the results table")
    filter_option = st.selectbox('Filter Status', ['All', 'short', 'long', 'close in mtp', 'pending'])
    sort_option = st.selectbox('Sort Results', ['Ticker','Lookback_perf','Yearly_perf',
                                'Avg_Vol','Candles_in_MTP', 'MTP_top_level', 'MTP_bottom_level',
                                'Market_Cap'], index = 7)
    is_ascending = st.checkbox('Sort Ascending?')
    
    
    #Filter logic
    if filter_option != 'All':
        mask = df_result['Status'] == filter_option
        df_filtered = df_result.loc[mask,:].copy()
    else:
        df_filtered = df_result.copy()
    
    
    #Sort logic
    df_filtered = df_filtered.sort_values(sort_option, ascending = is_ascending)
    
    #Number of rows to show
    df_show = df_filtered.head(num_of_rows)
    
    #Download buttons
    #-------------------------------------------------------------------------------
    st.subheader("")

    # Download button for the shown table
    df_show_csv = convert_df(df_show)
    st.download_button(
        label="Download shown table as CSV",
        data=df_show_csv,
        file_name='shown_table.csv',
        mime='text/csv',
    )
    
    
    # Download button for the full table
    df_filtered_csv = convert_df(df_filtered)
    st.download_button(
        label="Download full table as CSV",
        data=df_filtered_csv,
        file_name='full_table.csv',
        mime='text/csv',
    )
    
    
    
    #Download button for the not found tickers
    not_founds = pd.DataFrame(not_founds, columns = ['Not Found Tickers'])
    not_founds_csv = convert_df(not_founds)
    
    st.download_button("Download not found tickers as CSV", not_founds_csv,
                       file_name='not_founds.csv', mime='text/csv')
    
    
    #Show the result table
    st.subheader('')
    st.subheader('The Result Table')
    st.table(df_show)
    
    


    
    
    
    
    
    
# # Check results
# results = get_all_results(TICKER_LIST, PERFORMANCE_LOOKBACK, PRICE_TOP_LIMIT, PRICE_BOTTOM_LIMIT,
#                 ABS_LOW_POINT_WINDOW, ABS_HIGH_POINT_WINDOW,
#                 AVG_VOL_WINDOW, AVG_VOL_MIN,
#                 MTP_LOOKBACK, MTP_NUM_HBARS, MIN_CANDLES_FOR_MTP, MTP_RANGE_PERC)
# mask = results['Status'] == 'close in mtp'
# print(results[mask])

# ticker = 'BRK-A'
# df = get_data(ticker, PERFORMANCE_LOOKBACK)
# df_mtp = mtp(df, MTP_LOOKBACK, num_hbar = MTP_NUM_HBARS)
# df_area = get_mtp_area(df, df_mtp)




