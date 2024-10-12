from realnex_module import *
import pandas as pd

realnex_property_df = get_properties()
Properties_df = pd.DataFrame(realnex_property_df)
Properties_df['Search Address'] = Properties_df['AddressNumber1'] + " " + Properties_df['AddressDirection'] + " " + Properties_df['AddressStreet']
Properties_df.dropna(subset=['Search Address'], inplace=True)
Properties_df[['Key', 'Search Address']].to_csv("Property_address.csv", index=False)