import math

# adds vectors: x + y
def vector_add(x, y):
    return [x[i] + y[i] for i in range(len(x))]

# subtracts vectors: x - y
def vector_subtract(x, y):
    return [x[i] - y[i] for i in range(len(x))]

def vector_scale(x, a):
    return [x[i] * a for i in range(len(x))]

def vector_dot_product(x, y):
    return sum(x[i] * y[i] for i in range(len(x)))
    
def vector_length(x):
    return math.sqrt(vector_dot_product(x,x))
    
def vector_normalize(x):
    length = vector_length(x)
    return [x[i] / length for i in range(len(x))]
    
def vector_project_onto_plane(x, n):
    n_normalized = vector_normalize(n)
    d = vector_dot_product(x, n) / vector_length(n)
    p = [d * n_normalized[i] for i in range(len(n))]
    return [x[i] - p[i] for i in range(len(x))]

def vector_get_opposite(x):
    x = vector_normalize(x)
    return ([x[i]*-1 for i in range(len(x))])
    # p = sum([math.sqrt(x[i]**2) for i in range(len(x))])
    # return ([x[i]/p for i in range(len(x))]) #(x[0]/p,x[1]/p,x[2]/p)