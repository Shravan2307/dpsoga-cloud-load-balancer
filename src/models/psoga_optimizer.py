import numpy as np
from .cnn_lstm import CNNLSTM,train_model,predict
class CNNLSTMPSOGA:
 def __init__(self,Xtr,ytr,Xv,yv,seed=42,population_size=6,iterations=3): self.Xtr=Xtr;self.ytr=ytr;self.Xv=Xv;self.yv=yv;self.seed=seed;self.n=population_size;self.iterations=iterations
 def decode(self,z): return {'filters':[8,16,32][int(z[0])],'kernel_size':[2,3][int(z[1])],'pool_size':2,'hidden_units':[8,16,32][int(z[2])],'layers':1,'dropout':[0,.1][int(z[3])],'learning_rate':[.001,.003,.01][int(z[4])],'epochs':2,'batch_size':16}
 def run(self):
  rng=np.random.default_rng(self.seed);bounds=np.array([3,2,3,2,3]);pop=rng.integers(0,bounds,size=(self.n,5));best=None;bestf=1e9;hist=[]
  for _ in range(self.iterations):
   # GA selection/crossover/mutation is followed by PSO-like attraction to global best.
   fit=[]
   for z in pop:
    p=self.decode(z);arch={k:p[k] for k in ['filters','kernel_size','pool_size','hidden_units','layers','dropout']};m=CNNLSTM(self.Xtr.shape[2],**arch,output_size=self.ytr.shape[1]);train_model(m,self.Xtr,self.ytr,epochs=p['epochs'],lr=p['learning_rate'],batch_size=p['batch_size'],seed=self.seed);fit.append(float(np.mean(np.abs(predict(m,self.Xv)-self.yv))))
   i=int(np.argmin(fit))
   if fit[i]<bestf:bestf=fit[i];best=pop[i].copy()
   hist.append(bestf);order=np.argsort(fit);children=[pop[order[0]].copy()]
   while len(children)<self.n:
    a,b=pop[rng.choice(order[:max(2,self.n//2)],2,replace=False)];cut=int(rng.integers(1,5));c=np.r_[a[:cut],b[cut:]];mask=rng.random(5)<.15;c[mask]=rng.integers(0,bounds[mask]);children.append(c)
   pop=np.asarray(children);pop=np.rint(pop+.3*rng.random(pop.shape)*(best-pop)).astype(int).clip(0,bounds-1)
  return self.decode(best),bestf,hist
