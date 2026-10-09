from dataclasses import dataclass
import numpy as np
from .population import initialize_population,repair
@dataclass
class HybridResult:
    best_solution: np.ndarray
    best_fitness: float
    history: list
class HybridPSOGA:
    def __init__(self,objective,dimensions,upper_bound,population_size=24,crossover_rate=.9,mutation_rate=.06,c1=1.,c2=1.2,w=.7,iterations=20,seed=42):
        self.objective=objective;self.dimensions=dimensions;self.upper_bound=upper_bound;self.n=population_size;self.cr=crossover_rate;self.mr=mutation_rate;self.c1=c1;self.c2=c2;self.w=w;self.iterations=iterations;self.rng=np.random.default_rng(seed)
    def run(self):
        x=initialize_population(self.n,self.dimensions,self.upper_bound,self.rng).astype(float);v=np.zeros_like(x);p=x.copy();pf=np.array([self.objective(z) for z in p]);g=p[pf.argmin()].copy();gf=float(pf.min());history=[]
        for _ in range(self.iterations):
            order=np.argsort(pf); elite=p[order[0]].copy(); children=[elite]
            while len(children)<self.n:
                ia,ib=self.rng.integers(0,self.n,2);a=(p[ia] if pf[ia]<pf[ib] else p[ib]).copy();ia,ib=self.rng.integers(0,self.n,2);b=(p[ia] if pf[ia]<pf[ib] else p[ib]).copy()
                if self.rng.random()<self.cr:
                    cut=int(self.rng.integers(1,max(2,self.dimensions)));a,b=np.r_[a[:cut],b[cut:]],np.r_[b[:cut],a[cut:]]
                for z in (a,b):
                    mask=self.rng.random(self.dimensions)<self.mr;z[mask]=self.rng.integers(0,self.upper_bound,mask.sum())
                children.extend([a,b])
            x=np.asarray(children[:self.n]);r1=self.rng.random(x.shape);r2=self.rng.random(x.shape);v=self.w*v+self.c1*r1*(p-x)+self.c2*r2*(g-x);x=repair(x+v,self.upper_bound);f=np.array([self.objective(z) for z in x]);im=f<pf;p[im]=x[im];pf[im]=f[im];i=int(pf.argmin())
            if pf[i]<gf:g=p[i].copy();gf=float(pf[i])
            history.append(gf)
        return HybridResult(g.astype(int),gf,history)
