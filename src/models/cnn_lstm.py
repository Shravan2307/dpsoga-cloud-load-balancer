import numpy as np
try:
    import torch
    from torch import nn
except ImportError:
    torch = None

class CNNLSTM(nn.Module if torch else object):
    def __init__(self, input_size, filters=16, kernel_size=2, pool_size=2, hidden_units=16, layers=1, dropout=.1, output_size=None):
        if torch is None: raise ImportError('Install torch')
        super().__init__()
        self.output_size = output_size or input_size
        self.conv = nn.Conv1d(input_size, filters, kernel_size)
        self.pool = nn.MaxPool1d(pool_size)
        self.lstm = nn.LSTM(filters, hidden_units, layers, batch_first=True, dropout=dropout if layers > 1 else 0)
        self.fc = nn.Linear(hidden_units, self.output_size)
    def forward(self, x):
        x = self.pool(torch.relu(self.conv(x.transpose(1, 2))))
        return self.fc(self.lstm(x.transpose(1, 2))[0][:, -1])

def train_model(model, X, y, epochs=6, lr=.003, batch_size=16, seed=42):
    torch.manual_seed(seed); opt=torch.optim.Adam(model.parameters(), lr=lr); lossfn=nn.L1Loss()
    X=torch.tensor(X,dtype=torch.float32); y=torch.tensor(y,dtype=torch.float32); hist=[]
    for _ in range(epochs):
        model.train(); perm=torch.randperm(len(X)); total=0.0
        for ix in perm.split(batch_size):
            opt.zero_grad(); loss=lossfn(model(X[ix]),y[ix]); loss.backward(); opt.step(); total += float(loss.detach())*len(ix)
        hist.append(total/len(X))
    return hist

def predict(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X,dtype=torch.float32)).numpy()
