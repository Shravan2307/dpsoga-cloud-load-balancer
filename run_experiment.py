#!/usr/bin/env python3
import argparse,json,sys,time
from pathlib import Path
import numpy as np,pandas as pd,yaml
sys.path.insert(0,str(Path(__file__).parent))
from src.simulation.simulator import run_algorithm
from src.data.loader import load_dataset
from src.data.preprocessing import normalize,make_sequences,split
from src.models.cnn_lstm import CNNLSTM,train_model,predict
from src.models.psoga_optimizer import CNNLSTMPSOGA
from src.evaluation.metrics import mae
from src.visualization.plots import plot_comparison,plot_history

def phase1(args,cfg):
 p=cfg['phase1'];algs=[args.algorithm] if args.algorithm else p['algorithms'];rows=[]
 for a in algs: rows.append(run_algorithm(a,num_tasks=p['num_tasks'],num_vms=p['num_vms'],num_datacenters=p['num_datacenters'],hosts_per_datacenter=p['hosts_per_datacenter'],population_size=p['population_size'],iterations=p['iterations'],seed=args.seed))
 out=Path('results/tables');out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).drop(columns=['fitness_history']).to_csv(out/'phase1_results.csv',index=False);plot_comparison(pd.DataFrame(rows),'results/figures');plot_history(rows[-1]['fitness_history'],'results/figures');print(json.dumps(rows,indent=2));return rows

def phase2(args,cfg):
 p=cfg['phase2'];df=load_dataset(args.dataset or p['dataset'],args.google_path,n=p['train_points']+p['test_points'],seed=args.seed);a,sc=normalize(df);X,y=make_sequences(a,p['window']);(xt,yt),(xv,yv),(xe,ye)=split(X,y);base=CNNLSTM(X.shape[2],filters=16,kernel_size=2,pool_size=2,hidden_units=16,output_size=y.shape[1]);loss=train_model(base,xt,yt,epochs=p['epochs'],lr=.003,seed=args.seed);pred=predict(base,xe);base_mae=mae(ye,pred);opt=CNNLSTMPSOGA(xt,yt,xv,yv,seed=args.seed,population_size=p['optimizer_population'],iterations=p['optimizer_iterations']);params,val,hist=opt.run();arch={k:params[k] for k in ['filters','kernel_size','pool_size','hidden_units','layers','dropout']};best=CNNLSTM(X.shape[2],**arch,output_size=y.shape[1]);train_model(best,np.concatenate([xt,xv]),np.concatenate([yt,yv]),epochs=p['epochs'],lr=params['learning_rate'],batch_size=params['batch_size'],seed=args.seed);opt_mae=mae(ye,predict(best,xe));result={'dataset_label':'DEMO/SYNTHETIC DATASET' if (args.dataset or p['dataset'])=='synthetic' else 'REAL DATASET','baseline_cnn_lstm_mae':base_mae,'optimized_cnn_lstm_mae':opt_mae,'optimized_parameters':params,'optimizer_validation_mae':val,'training_loss':loss,'optimizer_history':hist};Path('results/tables').mkdir(parents=True,exist_ok=True);json.dump(result,open('results/tables/phase2_results.json','w'),indent=2);plot_history(hist,'results/figures','cnn_lstm_psoga_fitness_convergence');print(json.dumps(result,indent=2));return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['1','2']);ap.add_argument('--all',action='store_true');ap.add_argument('--algorithm',choices=['ga','pso','psoga']);ap.add_argument('--dataset',choices=['synthetic','google'],default=None);ap.add_argument('--google-path');ap.add_argument('--seed',type=int,default=42);a=ap.parse_args();cfg=yaml.safe_load(open('config/experiment.yaml'));np.random.seed(a.seed);Path('results/logs').mkdir(parents=True,exist_ok=True);json.dump({'seed':a.seed,'config':cfg},open('results/logs/run_config.json','w'),indent=2)
 if a.all or a.phase=='1' or a.algorithm: phase1(a,cfg)
 if a.all or a.phase=='2': phase2(a,cfg)
if __name__=='__main__':main()
