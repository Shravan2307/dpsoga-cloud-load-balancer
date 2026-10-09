import pandas as pd
def add_derived_features(df):
 out=df.copy();out['integrated_utilization']=out[['cpu','ram','storage','processing','bandwidth']].mean(axis=1);return out
