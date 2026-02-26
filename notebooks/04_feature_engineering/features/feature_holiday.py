import pandas as pd
import numpy as np

def generate_holiday_features(main_df, holidays_events_df, stores_df):
    """
    Tạo các đặc trưng về ngày lễ từ holidays_events.csv kết hợp với stores.csv 
    để áp dụng chính xác scope địa lý.
    
    Args:
        main_df: DataFrame chính chứa lịch sử giao dịch/doanh số (cần có 'date' và 'store_nbr').
        holidays_events_df: DataFrame từ holidays_events.csv.
        stores_df: DataFrame từ stores.csv.
        
    Returns:
        DataFrame đã được bổ sung các feature về holiday.
    """
    
    # 1. Tiền xử lý dữ liệu ngày tháng
    main_df['date'] = pd.to_datetime(main_df['date'])
    holidays_events_df['date'] = pd.to_datetime(holidays_events_df['date'])
    
    # 2. Xử lý Transferred Holidays
    # Nếu một ngày bị chuyển (transferred = True), ngày đó không thực sự là ngày nghỉ.
    # Ngày nghỉ thực tế sẽ nằm ở một dòng khác với type = 'Transfer'.
    # Tuy nhiên, để đơn giản, ta sẽ đánh dấu các ngày lễ thực sự được nghỉ.
    holidays_events_df['is_transferred'] = holidays_events_df['transferred'].astype(int)
    valid_holidays = holidays_events_df[holidays_events_df['transferred'] == False].copy()
    
    # 3. Mã hóa Holiday Type thành Numeric
    type_mapping = {'Holiday': 1, 'Event': 2, 'Additional': 3, 'Transfer': 4, 'Bridge': 5, 'Work Day': 0}
    valid_holidays['holiday_type_encoded'] = valid_holidays['type'].map(type_mapping).fillna(0)
    
    # 4. Tạo đặc trưng riêng cho Carnaval
    valid_holidays['is_carnaval'] = valid_holidays['description'].str.contains('Carnaval', case=False, na=False).astype(int)
    
    # 5. Kết hợp (Merge) để xác định Scope địa lý
    # Kết hợp main_df với stores_df để lấy city và state của từng store
    df = main_df.merge(stores_df[['store_nbr', 'city', 'state']], on='store_nbr', how='left')
    
    # Chuẩn bị DataFrame chứa các cờ holiday để merge
    holiday_features = []
    
    for _, row in valid_holidays.iterrows():
        h_date = row['date']
        h_type = row['type']
        h_locale = row['locale']
        h_locale_name = row['locale_name']
        h_encoded = row['holiday_type_encoded']
        is_transferred = row['is_transferred']
        is_carnaval = row['is_carnaval']
        
        # Xác định điều kiện áp dụng dựa trên locale
        if h_locale == 'National':
            mask = (df['date'] == h_date)
        elif h_locale == 'Regional':
            mask = (df['date'] == h_date) & (df['state'] == h_locale_name)
        elif h_locale == 'Local':
            mask = (df['date'] == h_date) & (df['city'] == h_locale_name)
        else:
            continue
            
        # Lưu trữ các mask hợp lệ để gán giá trị sau đó
        holiday_features.append({
            'mask': mask,
            'locale': h_locale,
            'is_transferred': is_transferred,
            'encoded_type': h_encoded,
            'is_carnaval': is_carnaval
        })

    # Khởi tạo các cột mặc định là 0
    df['is_national_holiday'] = 0
    df['is_regional_holiday'] = 0
    df['is_local_holiday'] = 0
    df['is_transferred_holiday'] = 0
    df['holiday_type'] = 0
    df['is_carnaval_feature'] = 0
    
    # Gán giá trị dựa trên các điều kiện đã tính toán
    for h in holiday_features:
        if h['locale'] == 'National':
            df.loc[h['mask'], 'is_national_holiday'] = 1
        elif h['locale'] == 'Regional':
            df.loc[h['mask'], 'is_regional_holiday'] = 1
        elif h['locale'] == 'Local':
            df.loc[h['mask'], 'is_local_holiday'] = 1
            
        df.loc[h['mask'], 'is_transferred_holiday'] = h['is_transferred']
        df.loc[h['mask'], 'holiday_type'] = h['encoded_type']
        df.loc[h['mask'], 'is_carnaval_feature'] = h['is_carnaval']

    # 6. Halo Effect Features (Hiệu ứng trước và sau ngày lễ)
    # Tìm tất cả các ngày có ít nhất một sự kiện ngày lễ (bất kể locale để tạo nhịp điệu mua sắm chung)
    unique_holiday_dates = valid_holidays['date'].drop_duplicates().sort_values().reset_index(drop=True)
    
    def get_days_to_next(date):
        future_holidays = unique_holiday_dates[unique_holiday_dates > date]
        if not future_holidays.empty:
            return (future_holidays.iloc[0] - date).days
        return -1 # Không có ngày lễ tiếp theo trong dữ liệu

    def get_days_after_last(date):
        past_holidays = unique_holiday_dates[unique_holiday_dates < date]
        if not past_holidays.empty:
            return (date - past_holidays.iloc[-1]).days
        return -1 # Không có ngày lễ trước đó trong dữ liệu

    # Tính toán áp dụng lên tập các ngày duy nhất trong data để tối ưu tốc độ
    unique_dates = df[['date']].drop_duplicates()
    unique_dates['days_to_next_holiday'] = unique_dates['date'].apply(get_days_to_next)
    unique_dates['days_after_last_holiday'] = unique_dates['date'].apply(get_days_after_last)
    
    # Merge lại vào dataframe chính
    df = df.merge(unique_dates, on='date', how='left')
    
    # 7. Earthquake Dummy (Tháng 4/2016)
    # Trận động đất lớn xảy ra vào ngày 16/04/2016. Tác động rõ rệt trong khoảng 1 tháng sau đó.
    earthquake_start = pd.to_datetime('2016-04-16')
    earthquake_end = pd.to_datetime('2016-05-16')
    df['is_earthquake_period'] = ((df['date'] >= earthquake_start) & (df['date'] <= earthquake_end)).astype(int)
    
    # Cleanup các cột không cần thiết
    df = df.drop(columns=['city', 'state'])
    
    return df

if __name__ == "__main__":
    df_train = pd.read_csv(r'train.csv')
    df_holidays = pd.read_csv(r'holidays_events_cleaned.csv')
    df_stores = pd.read_csv(r'stores_cleaned.csv')
    df_featured = generate_holiday_features(df_train, df_holidays, df_stores)
    print(df_featured.head())