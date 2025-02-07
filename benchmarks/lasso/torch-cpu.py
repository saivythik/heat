#!/usr/bin/env python

import argparse
import h5py
import time
import torch


class Lasso:
    def __init__(self, lam=0.1, max_iter=100, tol=1e-6):
        self.__lam = lam
        self.max_iter = max_iter
        self.tol = tol
        self.__theta = None
        self.n_iter = None

    @property
    def coef_(self):
        return None if self.__theta is None else self.__theta[1:]

    @property
    def intercept_(self):
        return None if self.__theta is None else self.__theta[0]

    @property
    def lam(self):
        return self.__lam

    @lam.setter
    def lam(self, arg):
        self.__lam = arg

    @property
    def theta(self):
        return self.__theta

    def soft_threshold(self, rho):
        if rho < -self.__lam:
            return rho + self.__lam
        elif rho > self.__lam:
            return rho - self.__lam
        else:
            return 0.0

    def rmse(self, gt, yest):
        return torch.sqrt((torch.mean((gt - yest) ** 2))).item()

    def fit(self, x, y):
        # get number of model parameters
        _, n = x.shape

        # initialize model parameters
        theta = torch.zeros(n, 1, device=x.device)
        # looping until max number of iterations or convergence
        for i in range(self.max_iter):
            theta_old = theta.clone()

            # looping through each coordinate
            for j in range(n):
                y_est = (x @ theta)[:, 0]

                rho = (x[:, j] * (y - y_est + theta[j] * x[:, j])).mean()

                # intercept parameter theta[0] not be regularized
                if j == 0:
                    theta[j] = rho
                else:
                    theta[j] = self.soft_threshold(rho)

            diff = self.rmse(theta, theta_old)
            if self.tol is not None:
                if diff < self.tol:
                    self.n_iter = i + 1
                    self.__theta = theta
                    break

        self.__theta = theta

    def predict(self, x):
        return (x @ self.__theta)[:, 0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyTorch lasso cpu benchmark")
    parser.add_argument("--file", type=str, help="file to benchmark")
    parser.add_argument("--dataset", type=str, help="dataset within file to benchmark")
    parser.add_argument("--labels", type=str, help="dataset within file pointing to the labels")
    parser.add_argument("--trials", type=int, help="number of benchmark trials")
    parser.add_argument("--iterations", type=int, help="iterations")
    args = parser.parse_args()

    print("Loading data... {}[{}]".format(args.file, args.dataset), end="")
    with h5py.File(args.file, "r") as handle:
        data = torch.Tensor(handle[args.dataset], device="cpu")
        labels = torch.Tensor(handle[args.labels], device="cpu")
    print("\t[OK]")

    for trial in range(args.trials):
        print("Trial {}...".format(trial), end="")
        lasso = Lasso(max_iter=args.iterations, tol=-1.0)
        start = time.perf_counter()
        lasso.fit(data, labels)
        end = time.perf_counter()
        print("\t{}s".format(end - start))
