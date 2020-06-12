from invoke import task

from . import csvs
from . import xlsx
from . import plot


@task(default=True)
def all(ctx, mode='development', output_root_dir=None):
    """
    Run all tasks in all files. (run.all, xlsx.all, csvs.all, plot.all)
    """
    csvs.all(ctx, mode=mode, output_root_dir=output_root_dir)
    xlsx.all(ctx, mode=mode, output_root_dir=output_root_dir)
    plot.all(ctx, mode=mode, output_root_dir=output_root_dir)
