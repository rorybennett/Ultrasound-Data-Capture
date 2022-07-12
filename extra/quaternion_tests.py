from pyquaternion import Quaternion
import numpy as np

p = [100, 100, 0]

q = [0.00372314453125, 0.6357421875, 0.771728515625, 0.011993408203125]

rpp = Quaternion(q).rotate(p)

print(f'Point: {p}, Rotated: {rpp}, Quaternion: {q}')

print(np.linalg.norm(p))
print(np.linalg.norm(rpp))
