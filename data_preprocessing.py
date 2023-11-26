import pandas as pd
import datetime as dt
import numpy as np


def read_data(path="Data/RFM_MEGAMAL_UPDATE.csv"):
    df = pd.read_csv(path, header=None)
    columns = ['id_factor', 'date', 'unit', 'price', 'id_customer', 'phone_number', 'customer_name']
    df.columns = columns
    return df


def make_rfm(df):
    # keep only the datas after 2021-08-01
    df = df[df['date'] > "2021-08-01"]
    # drop moshtarian megamal from df
    df = df[df['id_customer'] != 21604922]
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    # drop duplicates
    df = df.drop_duplicates()
    # Make total price of factor
    df['total_price'] = df['unit'] * df['price']
    # Select now date for calculate recency of customers
    now = dt.datetime(2023, 8, 30)
    # Create RFM dataframe based on recency date, Abundance id_factor and sum total_price
    rfm = df.groupby('id_customer').agg({'date': lambda day: (now - day.max()).days,
                                         'id_factor': lambda num: len(num),
                                         'total_price': lambda price: price.sum(),
                                         'phone_number': lambda number: number,
                                         'customer_name': lambda name:name,

                                         })
    col_list = ['recency', 'frequency', 'monetary', 'phone_number', 'customer_name']

    # Function to make all values unique
    def make_values_unique(value):
        if isinstance(value, (list, np.ndarray)):
            return [value[0]] if len(value) > 0 else []  # Keep only the first element in the array or list
        else:
            return value

    # Apply the function to the column
    rfm['phone_number'] = rfm['phone_number'].apply(make_values_unique)
    rfm['customer_name'] = rfm['customer_name'].apply(make_values_unique)
    rfm.columns = col_list
    return rfm


def make_rfm_scores(rfm):
    arr = np.array(rfm["recency"])
    arr.sort()
    Q1 = int(np.quantile(arr, 0.33))
    Q2 = int(np.quantile(arr, 0.66))

    def make_r(recency):
        r = 0
        if recency < Q1:
            r = 3
        elif Q1 <= recency <= Q2:
            r = 2
        elif recency >= Q2:
            r = 1
        return r

    rfm['R'] = rfm['recency'].apply(make_r)

    # Define the number of bins
    num_bins = 3

    # Automatically create bin edges
    bin_edges = pd.cut(rfm['frequency'], bins=num_bins, labels=False)

    # Define a function to handle values outside the specified bin edges
    def assign_value(value, num_bins):
        if value < 0:
            return 1  # Assign to the lowest bin
        elif value >= num_bins:
            return num_bins  # Assign to the highest bin
        else:
            return value + 1  # Adding 1 to start the values from 1 instead of 0

    # Create the 'F' column based on automatic binning
    rfm['F'] = bin_edges.apply(lambda x: assign_value(x, num_bins))

    # Make monetary column
    arr = np.array(rfm["monetary"])
    arr.sort()
    Q1 = int(np.quantile(arr, 0.33))
    Q2 = int(np.quantile(arr, 0.66))

    def make_m(monetary):
        m = 0
        if monetary < Q1:
            m = 1
        elif Q1 <= monetary < Q2:
            m = 2
        elif monetary >= Q2:
            m = 3
        return m

    rfm['M'] = rfm['monetary'].apply(make_m)
    # Create RFM score columns with put together R and F and M values
    rfm["RFM_Score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    # create title for each group od customers based on their points and behaviours it could be changed
    seg_map = {
        r'[1][1][1]': 'Lost Cheap Customers',
        r'[1][1-3][2-3]': 'Lost Valuable Customers',
        r'[2][1-3][2-3]': 'Need Attention (Normal Customers)',
        r'3[1][1]': 'New Customers',
        r'3[1-3][2-3]': "Potential To Be Best",
        r'333': 'Best Customers',
    }
    rfm['Segment'] = rfm['R'].astype(str) + rfm['F'].astype(str) + rfm['M'].astype(str)
    rfm['Segment'] = rfm['Segment'].replace(seg_map, regex=True)
    rfm['Segment'] = rfm['Segment'].apply(
        lambda x: "Others" if x not in ('Lost Cheap Customers', 'Lost Valuable Customers',
                                        'Need Attention (Normal Customers)', 'New Customers',
                                        'Potential To Be Best', 'Best Customers') else x)
    rfm = rfm.reset_index()
    return rfm




#
# df = read_data()
# rfm = make_rfm(df)
# rfm_scores = make_rfm_scores(rfm)
# print(rfm_scores[rfm_scores['Segment'] == "Others"]['RFM_Score'].unique())
# category_counts = rfm['Segment'].value_counts()
# grouped = rfm[['recency', 'frequency', 'monetary']].groupby(rfm['Segment']).mean().sort_values('monetary')
# print(grouped)
# print(category_counts)

# print(rfm_scores[rfm_scores['Segment'] == 'Loyal Customers'])

# import plotly.express as px
# segment_product_counts = rfm_scores.groupby('Segment').size().reset_index(name='Count')
# segment_product_counts = segment_product_counts.sort_values('Count', ascending=False)
#
# fig_treemap_segment_product = px.treemap(segment_product_counts,
#                                          path=['Segment'],
#                                          values='Count',
#                                          color='Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
#                                          title='RFM Customer Segments by Value',
#                                          branchvalues='total')  # Normalize sizes based on total count
#
# # Adjust the size of the plot
# fig_treemap_segment_product.update_layout(
#     width=800,  # Adjust width as needed
#     height=600,  # Adjust height as needed
#     margin=dict(l=50, r=0, b=0, t=40)  # Adjust margin if needed
# )
#
# # Show the plot
# fig_treemap_segment_product.show()
