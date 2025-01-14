import cupy as cp
x_gpu = cp.array([1, 2, 3])
print(x_gpu.device)
l2_gpu = cp.linalg.norm(x_gpu)
print(l2_gpu)
