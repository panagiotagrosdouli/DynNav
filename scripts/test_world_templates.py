import numpy as np
from world_templates import world_bottleneck, world_culdesac, world_noisy_corridor

base_grid = np.zeros((50, 50))

bottleneck_grid, meta_b = world_bottleneck(base_grid)
culdesac_grid, meta_c = world_culdesac(base_grid)
noisy_grid, meta_n = world_noisy_corridor(base_grid)

print(meta_b)
print(meta_c)
print(meta_n)
