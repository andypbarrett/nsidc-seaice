# Command line interface to generate latest daily files
from multiprocessing import Pool
from subprocess import run
import os

import click

from seaice import version_flag
import seaice.nasateam as nt
import seaice.logging as seaicelogging


log = seaicelogging.init('seaice.images')
DEFAULT_OUTPUT = os.path.join(nt.SEA_ICE_BASE_DIR, 'images')


@click.command()
@version_flag
@click.option('--extent', is_flag=True, help=(
    'Set this flag to generate extent imagery'))
@click.option('--concentration', is_flag=True, help=(
    'Set this flag to generate concentration imagery'))
@click.option('--anomaly', is_flag=True, help=(
    'Set this flag to generate anomaly imagery'))
@click.option('--trend', is_flag=True, help=(
    'Set this flag to generate trend imagery'))
@click.option('--allow_bad_data', is_flag=True, help=(
    'Set this flag to set the allow_bad_data option'
    ' on the image generation commands'))
@click.option('--north', 'hemisphere', flag_value='-h N', help=(
    'Generate imagery for northern hemisphere only'))
@click.option('--south', 'hemisphere', flag_value='-h S', help=(
    'Generate imagery for southern hemisphere only'))
@click.option('--both', 'hemisphere', flag_value='-h N,S', default=True, help=(
    'Generate imagery for both hemispheres'))
@click.option('--output', default=DEFAULT_OUTPUT, help=(
    'Output directory for image generation commands'))
@click.option('--daily', 'temporality', flag_value='--daily', help=(
    'Generate daily images'))
@click.option('--monthly', 'temporality', flag_value='--monthly', default=True, help=(
    'Generate monthly images'))
@click.option('--hires/--no-hires', is_flag=True, default=True,
              help=('Generate high resolution images in addition to the normal outputs.'))
@click.option('--blue_marble', is_flag=True,
              help=('Generate blue marble images; has no effect unless at least '
                    'one of --extent and --concentration are used.'))
@click.option('--google', is_flag=True,
              help=('Generate Google earth images; has no effect unless --extent is used.'))
@click.option('--geotiff', is_flag=True,
              help=('Generate Geotiff images; has no effect unless --extent, '
                    '--concentration or --anomaly is used.'))
@click.option('--latest', default=1, type=int,
              help=('The number of images of each type to create.'))
@click.option('--dev', is_flag=True, default=False,
              help=('Run the sii_image commands with `python -m`, so that this command '
                    'can be run from source.'))
@seaicelogging.log_command(log)
def sii_image_latest(extent, concentration, anomaly, trend,
                     allow_bad_data, hemisphere, output, temporality, hires, blue_marble, google,
                     geotiff, latest, dev):
    """Run latest daily or monthly image generation"""

    allow_bad_data = '--allow-bad-data' if allow_bad_data else ''

    config = {'hemisphere': hemisphere, 'allow_bad_data': allow_bad_data,
              'temporality': temporality, 'output': output, 'latest': latest}

    command_options = {'extent': extent, 'concentration': concentration,
                       'anomaly': anomaly, 'trend': trend}
    commands = []

    hires_flags = ['']
    if hires:
        hires_flags.append('--hires')

    sii_image_executable = '{}sii_image'.format('python -m seaice.images.cli.' if dev else '')
    sii_geotiff_executable = '{}sii_image_geotiff'.format('python -m seaice.images.cli.' if dev
                                                          else '')

    for command in [key for key, val in command_options.items() if val is True]:
        special_flags = ['']
        if blue_marble and (command in ('extent', 'concentration')):
            special_flags.append('--blue_marble')

        for special_flag in special_flags:
            for hires_flag in hires_flags:
                cmd = ('{executable} {hemisphere} --{command} {temporality} --latest {latest} '
                       '{allow_bad_data} --output {output} {special} '
                       '{hires}').format(**config, **{'command': command,
                                                      'special': special_flag,
                                                      'hires': hires_flag,
                                                      'executable': sii_image_executable})
                commands.append(cmd)

        # Geotiffs
        if geotiff and (command in ('extent', 'concentration', 'anomaly')):
            cmd = ('{executable} {hemisphere} --{command} {temporality} --latest {latest} '
                   '{allow_bad_data} --output '
                   '{output}').format(**config,
                                      **{'executable': sii_geotiff_executable,
                                         'command': command})
            commands.append(cmd)

    if google:
        if output == DEFAULT_OUTPUT:
            google_out = ''  # use the google_earth cli's default
        else:
            google_out = '-o {}'.format(output)

        executable = '{}sii_image_google_earth'.format(
            'python -m seaice.images.cli.' if dev else ''
        )
        cmd = ('{executable} --latest {latest} {allow_bad_data} '
               '{google_out}').format(**config, **{'executable': executable,
                                                   'google_out': google_out})
        commands.append(cmd)

    with Pool() as p:
        p.map(_run_command, commands)


def _run_command(cmd):
    print(cmd)
    run(cmd.split())


if __name__ == '__main__':
    sii_image_latest()
