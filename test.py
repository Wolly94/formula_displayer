from basics import *
import copy

class A:
    def __init__(self, a):
        self.a = a

def f(a):
    a.a = 4

a = A(5)
b = copy.copy(a)
f(b)
print(a.a, b.a)
