import numpy as np
def initialize_population(size, dimensions, upper_bound, rng): return rng.integers(0, upper_bound, size=(size,dimensions), endpoint=False)
def repair(position, upper_bound): return np.asarray(np.rint(position),dtype=int).clip(0,upper_bound-1)
