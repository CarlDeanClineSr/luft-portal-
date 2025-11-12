#!/usr/bin/env python3
"""
Starter ML script for foam fits (emulator + inference).

Modes:
 - synth   : generate synthetic switching histograms given params
 - train   : train a small emulator NN on synth data
 - infer   : run inference on observed histogram using emulator + MCMC

This is a minimal skeleton. Expand the simulator and inference as needed.
"""
import argparse
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

# Simple simulator: given params produce a summary vector (eg: binned counts)
def simulate_switching(Ic=2e-6, C=2e-12, f=0.0, N=2000, rng=None):
    # placeholder: create synthetic histogram with a mean Isw that shifts with f
    if rng is None:
        rng = np.random.RandomState(1)
    mu = Ic * (1.0 + f)  # toy mapping
    sigma = Ic * 0.02
    samples = rng.normal(loc=mu, scale=sigma, size=N)
    hist, edges = np.histogram(samples, bins=50, range=(0, Ic*1.5))
    return hist.astype(np.float32) / N  # normalized histogram (summary)

# Simple emulator network
class Emulator(nn.Module):
    def __init__(self, hist_bins=50):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hist_bins, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)  # predict f
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

def synth_mode(args):
    rng = np.random.RandomState(42)
    X = []
    Y = []
    for i in range(args.nsamp):
        f = rng.uniform(-0.1, 0.1)
        hist = simulate_switching(Ic=args.Ic, C=args.C, f=f, N=args.N, rng=rng)
        X.append(hist)
        Y.append(f)
    X = np.stack(X)
    Y = np.array(Y, dtype=np.float32)
    np.savez(args.out, X=X, Y=Y)
    print("Wrote synth data to", args.out)

def train_mode(args):
    data = np.load(args.data)
    X = data['X']
    Y = data['Y']
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Emulator(hist_bins=X.shape[1]).to(device)
    opt = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    Xt = torch.tensor(X, dtype=torch.float32).to(device)
    Yt = torch.tensor(Y, dtype=torch.float32).to(device)
    for epoch in range(args.epochs):
        model.train()
        opt.zero_grad()
        preds = model(Xt)
        loss = loss_fn(preds, Yt)
        loss.backward()
        opt.step()
        if epoch % 10 == 0:
            print(f"Epoch {epoch} loss {loss.item():.5e}")
    torch.save(model.state_dict(), args.model)
    print("Saved model to", args.model)

def infer_mode(args):
    # load observed histogram
    df = pd.read_csv(args.obs)
    if 'I_sw' in df.columns:
        # produce histogram summary
        hist, edges = np.histogram(df['I_sw'].values, bins=50, range=(0, args.Ic*1.5))
        Xobs = hist.astype(np.float32) / len(df)
    else:
        raise RuntimeError("Expected column I_sw in observed CSV")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Emulator(hist_bins=Xobs.shape[0]).to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()
    with torch.no_grad():
        x = torch.tensor(Xobs[None,:], dtype=torch.float32).to(device)
        f_hat = model(x).item()
    print(f"Point estimate f_hat = {f_hat:.5f}")
    # TODO: add MCMC/uncertainty via emulator likelihood or direct sampling

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=['synth','train','infer'], required=True)
    p.add_argument("--out", default="ml/train_data.npz")
    p.add_argument("--data", default="ml/train_data.npz")
    p.add_argument("--model", default="ml/emulator.pt")
    p.add_argument("--obs", default="data/mit2007_digitized_histogram.csv")
    p.add_argument("--nsamp", type=int, default=2000)
    p.add_argument("--N", type=int, default=2000)
    p.add_argument("--Ic", type=float, default=2e-6)
    p.add_argument("--C", type=float, default=2e-12)
    p.add_argument("--epochs", type=int, default=100)
    args = p.parse_args()
    if args.mode == 'synth':
        synth_mode(args)
    elif args.mode == 'train':
        train_mode(args)
    elif args.mode == 'infer':
        infer_mode(args)

if __name__ == "__main__":
    main()
