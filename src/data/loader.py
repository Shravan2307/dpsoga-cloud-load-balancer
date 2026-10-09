from pathlib import Path
import numpy as np,pandas as pd
FEATURES=['cpu','ram','storage','processing','bandwidth']
def synthetic_dataset(n=240,seed=42):
 r=np.random.default_rng(seed);t=np.arange(n);base=np.column_stack([.5+.2*np.sin(t/12+i)+.04*r.normal(size=n) for i in range(5)]);return pd.DataFrame(np.clip(base,0,1),columns=FEATURES)
def load_google_trace(path):
 p=Path(path)
 if not p.exists(): raise FileNotFoundError(f'Google Cluster Workload Traces are not bundled. Download the trace and pass its local path: {path}')
 df=pd.read_csv(p); aliases={'memory':'ram','mem':'ram','disk':'storage','cpu_utilization':'cpu','processing_power':'processing','bw':'bandwidth'};df=df.rename(columns={c:aliases.get(c,c) for c in df.columns});missing=[c for c in FEATURES if c not in df]
 if missing: raise ValueError(f'Trace must provide columns {FEATURES}; missing {missing}')
 return df[FEATURES].apply(pd.to_numeric,errors='coerce').interpolate().bfill().ffill()
def load_dataset(kind='synthetic',path=None,**kw): return synthetic_dataset(**kw) if kind=='synthetic' else load_google_trace(path)
