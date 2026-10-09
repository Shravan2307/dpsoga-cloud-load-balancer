import numpy as np
def normalize(df):
 a=df.to_numpy(float);lo=a.min(0);hi=a.max(0);return (a-lo)/np.maximum(hi-lo,1e-9),{'min':lo.tolist(),'max':hi.tolist()}
def make_sequences(a,window=5,target=None):
 target=a if target is None else target;X=np.array([a[i-window:i] for i in range(window,len(a))]);y=np.array([target[i] for i in range(window,len(a))]);return X,y
def split(X,y,train=.7,val=.15):
 n=len(X);a=int(n*train);b=int(n*(train+val));return (X[:a],y[:a]),(X[a:b],y[a:b]),(X[b:],y[b:])
