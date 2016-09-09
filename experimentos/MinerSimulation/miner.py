from statistics import mean, median, stdev
from math import log
from numpy.random import exponential
import matplotlib.pyplot as plt
import numpy as np
import string
import random

def rndExp(x):
  return -log(1.0 - random.random()) / float(x)

def sample1(x, size):
  return [rndExp(x) for i in range(size)]
  
def sample2(x, size):
  return list(exponential(x, size))
  
def accumulated(xs):
  val = 0
  ls = []
  for x in xs:
    val += x
    ls.append(val)
  return ls
  
def deaccumulate(xs):
  ls = [xs[0]]
  for i in range(1, len(xs)):
    ls.append(xs[i] - xs[i-1])
  return ls
  
def hist(a, b, s):
  plt.hist(a, bins=range(0, 60000, 1000), facecolor='y', cumulative=False)
  plt.hist(b, bins=range(0, 60000, 1000), facecolor='b', cumulative=False)
  plt.hist(s, bins=range(0, 60000, 1000), facecolor='orange', cumulative=False, alpha=0.30)
  plt.show()
  
def graph(a, b, joined):
  a = a[:10]
  b = b[:10]
  
  C = joined[:10]
  A = [x for x in a if x in C]
  B = [x for x in b if x in C]

  Ay = [2 for x in A]
  By = [0 for x in B]
  Cay = [1 for x in A]
  Cby = [1 for x in B]
  
  fig = plt.figure(figsize=(25,7))
  plt.ylim((-0.2,2.2))
  plt.tick_params(axis='y', which='major', labelsize=20)
  plt.yticks([0, 1, 2], ['Minero 1', 'Minado de la Red\n(Minero 1 + Minero 2)' , 'Minero 2'], rotation=30)
  
  plt.axhline(y=0, xmin=0, xmax=C[-1], hold=None, c="black")
  plt.axhline(y=1, xmin=0, xmax=C[-1], hold=None, c="black")
  plt.axhline(y=2, xmin=0, xmax=C[-1], hold=None, c="black")
  plt.scatter(A, Ay, color='orange', s=800)
  plt.scatter(B, By, color='gray', s=800)
  plt.scatter(A, Cay, color='orange', s=800)
  plt.scatter(B, Cby, color='gray', s=800)
  
  plt.xlabel('Tiempo (ms)', fontsize=20)
  plt.title('Suma de los procesos de Poisson\nSimulación de tiempos de minado', fontsize=20)
  
  plt.xlim((0, C[-1]))
  
  plt.savefig(filename=("/tmp/saraza%d.png" % random.randint(1, 1000)), transparent=True)
  plt.clf()

def simulateTwoMiners():
  numblocks = 20000
  s1 = sample2((10000 / log(2))/.5, numblocks)
  s2 = sample2((10000 / log(2))/.5, numblocks)
  
  a1 = accumulated(s1)
  a2 = accumulated(s2)
  s3 = sorted(a1+a2)
  
  #graph(a1, a2, s3)
  
  k3 = deaccumulate(s3)
  #hist(s1, s2, s1+s2)
  print("Median: %.4f, Mean: %.4f, StdDev: %.4f" % (median(s1), mean(s1), stdev(s1)))
  print("Median: %.4f, Mean: %.4f, StdDev: %.4f" % (median(s2), mean(s2), stdev(s2)))
  print("Median: %.4f, Mean: %.4f, StdDev: %.4f" % (median(k3), mean(k3), stdev(k3)))

  s = s3[:1000]
  time = max(s)
  
  print("Mining %d blocks took %.2f s" % (numblocks, time/1000))
  

def main():
  s1 = sample1(1.0/10000, 10000)
  s2 = sample2(10000, 10000)
  
  #print("Median: %.4f, Mean: %.4f, StdDev: %.4f" % (median(s1), mean(s1), stdev(s1)))
  #print("Median: %.4f, Mean: %.4f, StdDev: %.4f" % (median(s2), mean(s2), stdev(s2)))
  simulateTwoMiners()


if __name__ == "__main__":
  main()
