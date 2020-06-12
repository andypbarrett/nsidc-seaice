from invoke import Collection
from musher import build
from musher import clean
from musher import deploy

from . import test


ns = Collection()
ns.add_collection(build)
ns.add_collection(clean)
ns.add_collection(deploy)
ns.add_collection(test)

#########################################################################
# WARNING: All tasks that import from seaice code must be commented for #
# publishing to anaconda.org to work properly in the current CircleCI   #
# configuration. See: https://circleci.com/bb/nsidc/seaice/341          #
# TODO: Fix this and remove this warning.                               #
#########################################################################

# seaiceshapefiles
# from . import generate

# seaice.tools
# from . import csvs
# from . import plot
# from . import run
# from . import xlsx

# sedna
# from . import sedna


# seaiceshapefiles
# ns.add_collection(generate)

# seaice.tools
# ns.add_collection(csvs)
# ns.add_collection(plot)
# ns.add_collection(run)
# ns.add_collection(xlsx)

# seaice.sedna
# ns.add_collection(sedna)
