import numpy as np
def mae(y_true,y_pred): return float(np.mean(np.abs(np.asarray(y_true)-np.asarray(y_pred))))
def classification_metrics(y_true,y_pred):
 yt=np.asarray(y_true).astype(int);yp=np.asarray(y_pred).astype(int);tp=((yt==1)&(yp==1)).sum();tn=((yt==0)&(yp==0)).sum();fp=((yt==0)&(yp==1)).sum();fn=((yt==1)&(yp==0)).sum();precision=tp/max(tp+fp,1);recall=tp/max(tp+fn,1);return {'precision':float(precision),'recall':float(recall),'f1_score':float(2*precision*recall/max(precision+recall,1e-12)),'accuracy':float((tp+tn)/max(len(yt),1))}
