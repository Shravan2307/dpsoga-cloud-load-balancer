from pathlib import Path
import matplotlib.pyplot as plt
def plot_comparison(df,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 for metric in ['average_waiting_time','makespan','migration_count','running_time','energy_kwh','cpu_utilization','ram_utilization','storage_utilization']:
  if metric in df:
   ax=df.plot.bar(x='algorithm',y=metric,legend=False,title=metric.replace('_',' ').title());ax.figure.tight_layout();ax.figure.savefig(out/f'{metric}.png',dpi=140);plt.close(ax.figure)
def plot_history(history,out,name='psoga_fitness_convergence'):
 Path(out).mkdir(parents=True,exist_ok=True);plt.plot(history);plt.xlabel('Iteration');plt.ylabel('Best objective');plt.title(name);plt.tight_layout();plt.savefig(Path(out)/f'{name}.png',dpi=140);plt.close()
