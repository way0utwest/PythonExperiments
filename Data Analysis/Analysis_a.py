import os
import numpy as np
import pandas as pd 

os.chdir("E:\Documents\git\PythonExperiments\Data Analysis")

sales = pd.read_csv("data\sales_data.csv")

sales['Cost'].head()


sales['Cost'] *= 1.05
sales['Cost'].head()


sales.loc[sales['State'] == 'New York']

sales.loc[['State' == 'New York']]

sales[['State'] == 'New York']

sales for sales['State'] == 'New York']

