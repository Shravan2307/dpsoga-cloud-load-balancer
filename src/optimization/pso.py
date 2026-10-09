from dataclasses import dataclass
import numpy as np
from .population import initialize_population,repair
@dataclass
class PSOResult:
    best_solution: np.ndarray
    best_fitness: float
    history: list
class ParticleSwarmOptimizer:
    def __init__(self,objective,dimensions,upper_bound,population_size=24,c1=1.0,c2=1.2,w=.7,iterations=20,seed=42):
        self.objective=objective;self.dimensions=dimensions;self.upper_bound=upper_bound;self.population_size=population_size;self.c1=c1;self.c2=c2;self.w=w;self.iterations=iterations;self.rng=np.random.default_rng(seed)
    def run(self):
        x=initialize_population(self.population_size,self.dimensions,self.upper_bound,self.rng).astype(float);v=np.zeros_like(x);p=x.copy();pf=np.array([self.objective(z) for z in p]);gi=int(pf.argmin());g=p[gi].copy();gf=float(pf[gi]);history=[]
        for _ in range(self.iterations):
            r1=self.rng.random(x.shape);r2=self.rng.random(x.shape);v=self.w*v+self.c1*r1*(p-x)+self.c2*r2*(g-x);x=repair(x+v,self.upper_bound);f=np.array([self.objective(z) for z in x]);im=f<pf;p[im]=x[im];pf[im]=f[im];gi=int(pf.argmin());
            if pf[gi]<gf:g=p[gi].copy();gf=float(pf[gi])
            history.append(gf)
        return PSOResult(g.astype(int),gf,history)
