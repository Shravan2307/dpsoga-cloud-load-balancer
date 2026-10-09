from dataclasses import dataclass
import numpy as np
from .population import initialize_population
@dataclass
class OptimizationResult:
    best_solution: np.ndarray
    best_fitness: float
    history: list
class GeneticAlgorithm:
    def __init__(self, objective, dimensions, upper_bound, population_size=24, crossover_rate=.9, mutation_rate=.06, iterations=20, seed=42):
        self.objective,self.dimensions,self.upper_bound=objective,dimensions,upper_bound; self.population_size=population_size; self.crossover_rate=crossover_rate; self.mutation_rate=mutation_rate; self.iterations=iterations; self.rng=np.random.default_rng(seed)
    def _select(self,pop,fit):
        ids=self.rng.integers(0,len(pop),size=2); return pop[ids[np.argmin(fit[ids])]].copy()
    def _crossover(self,a,b):
        if self.rng.random()>self.crossover_rate or self.dimensions<2:return a,b
        p=int(self.rng.integers(1,self.dimensions)); return np.r_[a[:p],b[p:]],np.r_[b[:p],a[p:]]
    def _mutate(self,x):
        mask=self.rng.random(self.dimensions)<self.mutation_rate; x[mask]=self.rng.integers(0,self.upper_bound,size=mask.sum()); return x
    def run(self):
        pop=initialize_population(self.population_size,self.dimensions,self.upper_bound,self.rng); best=None; bestf=float('inf'); history=[]
        for _ in range(self.iterations):
            fit=np.array([self.objective(x) for x in pop]); i=int(fit.argmin())
            if fit[i]<bestf:bestf=float(fit[i]);best=pop[i].copy()
            history.append(bestf); new=[best.copy()]
            while len(new)<self.population_size:
                a,b=self._crossover(self._select(pop,fit),self._select(pop,fit));new.extend([self._mutate(a),self._mutate(b)])
            pop=np.asarray(new[:self.population_size])
        return OptimizationResult(best,bestf,history)
