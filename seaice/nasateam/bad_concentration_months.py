from .hemispheres import NORTH


# list of tuples (year, month, nt_hemi) where the monthly concentration gridset
# should be the empty gridset, but no other gridsets should be affected
#
# In the northern hemisphere, 1987-08 has a significant pole hole change 2/3
# through the month and therefore the monthly concentration grid should not be
# used. The extent grid is fine since the pole hole is filled up the same
# regardless of its size. The anomaly and trend grids are fine since they take
# the largest pole hole available in the years being compared.
BAD_CONCENTRATION_MONTHS = [(1987, 8, NORTH)]
