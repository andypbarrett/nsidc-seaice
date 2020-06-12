import os
import shutil
from unittest import TestCase
import glob
from subprocess import run

from click.testing import CliRunner

from seaice.images.cli.sii_image import sii_image
from seaice.images.cli.sii_image_geotiff import sii_image_geotiff
from seaice.images.cli.sii_image_google_earth import sii_image_google_earth
from seaice.images.cli.sii_image_sos import sii_image_sos
from seaice.nasateam import VERSION_STRING as version


class TestCLISeaiceImages(TestCase):
    output_dir = 'smoke_test_output'
    proof_dir = 'sample_images'
    reference_dir = 'reference_images'
    runner = CliRunner()

    def run_command(self, options_str):
        self.runner.invoke(sii_image, options_str.split(' '), catch_exceptions=False)

    def assert_files_exist(self, files):
        for file in files:
            file = os.path.join(self.output_dir, file)
            self.assertTrue(os.path.exists(file))

    def removeDir(self, dir):
        try:
            shutil.rmtree(dir)
        except FileNotFoundError:
            pass

    def moveOutput(self):
        test_method = self._testMethodName
        if not os.path.exists(self.proof_dir):
            os.mkdir(self.proof_dir)
        for filepath in glob.glob(os.path.join(self.output_dir, '*.png')):
            dir, filename = os.path.split(filepath)
            shutil.move(filepath,
                        os.path.join(self.proof_dir, '{}_{}'.format(test_method, filename)))

    @classmethod
    def setUpClass(cls):
        cls.removeDir(cls, cls.proof_dir)
        os.mkdir(cls.proof_dir)

    @classmethod
    def tearDownClass(cls):
        proof_images = glob.glob(os.path.join(cls.proof_dir, '*.png'))
        proof_images = [os.path.split(filepath)[1] for filepath in proof_images]
        f = open(os.path.join(cls.proof_dir, '..', 'smoke_test.html'), 'w')
        f.write('<html><head></head><body bgcolor="gray"><ul>')

        links = []
        for file in proof_images:
            links.append('<tr><td>{0}</td><td>{1}</td></tr><tr><td><img src="{0}"/>'
                         '</td><td><img src="{1}"/></td></tr>'.format(
                             os.path.join(cls.proof_dir, file),
                             './{}/{}'.format(cls.reference_dir, file)))
        links = sorted(links)
        links = ['<table>'] + links + ['</table>']
        f.writelines(links)

    def setUp(self):
        self.removeDir(self.output_dir)
        os.mkdir(self.output_dir)

    def tearDown(self):
        self.moveOutput()
        self.removeDir(self.output_dir)

    def test_creates_daily_concentration_images(self):
        self.run_command('-h N,S --daily -y 2012 -m 3 -d 14 -o {}'
                         ' --flatten'.format(self.output_dir))
        file_names = ['N_20120314_conc_{}.png'.format(version),
                      'S_20120314_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_monthly_concentration_images(self):
        self.run_command('-h N,S --monthly -y 2012 -m 3 -o {} --flatten'.format(self.output_dir))
        file_names = ['N_201203_conc_{}.png'.format(version),
                      'S_201203_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_daily_extent_images(self):
        self.run_command('-h N,S --extent --daily -y 2012 -m 3 -d 14 -o {}'
                         ' --flatten'.format(self.output_dir))
        file_names = ['N_20120314_extn_{}.png'.format(version),
                      'S_20120314_extn_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_monthly_extent_images(self):
        self.run_command('-h N,S --extent --monthly -y 2012 -m 3 -o {} '
                         '--flatten'.format(self.output_dir))
        file_names = ['N_201203_extn_{}.png'.format(version),
                      'S_201203_extn_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_daily_no_data_images(self):
        self.run_command('--daily --concentration -h N,S -o {} --flatten '
                         '-y 1979 -m 9 -d 22'.format(self.output_dir))
        file_names = ['N_19790922_conc_{}.png'.format(version),
                      'S_19790922_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_monthly_no_data_images(self):
        self.run_command('--monthly --concentration -h N,S -o {} --flatten '
                         '-y 1988 -m 1'.format(self.output_dir))
        file_names = ['N_198801_conc_{}.png'.format(version),
                      'S_198801_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_all_missing_images(self):
        self.run_command('--daily --concentration -h N,S -o {} --flatten '
                         '-y 1978 -m 11 -d 12 --allow-bad-data'.format(self.output_dir))
        file_names = ['N_19781112_conc_{}.png'.format(version),
                      'S_19781112_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_creates_image_with_missing_data(self):
        self.run_command('--daily --concentration -h N,S -o {} --flatten '
                         '-y 2016 -m 9 -d 9 -s 1.8'.format(self.output_dir))
        file_names = ['N_20160909_conc_{}.png'.format(version)]
        self.assert_files_exist(file_names)

    def test_generates_image_range(self):
        self.run_command('-h N --extent --monthly --flatten'
                         ' --range 20110101,20110401 -o {}'.format(self.output_dir))
        self.assert_files_exist(['N_201101_extn_{}.png'.format(version),
                                 'N_201102_extn_{}.png'.format(version),
                                 'N_201103_extn_{}.png'.format(version),
                                 'N_201104_extn_{}.png'.format(version)])

    def test_creates_monthly_concentration_anomly_image_north_missing(self):
        self.run_command('--monthly --anomaly -y 1987 -m 12 -h N -f -o {}'.format(self.output_dir))
        self.assert_files_exist(['N_198712_anom_{}.png'.format(version)])

    def test_creates_monthly_concentration_anomaly_image_north(self):
        self.run_command('-h N --anomaly --monthly -y 2011 -m 1 --flatten'
                         ' --year-range 1981,2010 -o {}'.format(self.output_dir))
        self.assert_files_exist(['N_201101_anom_{}.png'.format(version)])

    def test_creates_monthly_concentration_anomaly_image_south(self):
        self.run_command('-h S --anomaly --monthly -y 2011 -m 1 --flatten'
                         ' --year-range 1981,2010 -o {}'.format(self.output_dir))
        self.assert_files_exist(['S_201101_anom_{}.png'.format(version)])

    def test_creates_daily_extent_blue_marble_image_north(self):
        self.run_command('-h N --extent --blue_marble --daily -y 2011 -m 1 --flatten'
                         ' -d 12 -o {}'.format(self.output_dir))
        self.assert_files_exist(['N_20110112_extn_blmrbl_{}.png'.format(version)])

    def test_creates_monthly_extent_blue_marble_image_south(self):
        self.run_command('-h S --extent --blue_marble --monthly -y 2011 -m 1 --flatten'
                         ' -o {}'.format(self.output_dir))
        self.assert_files_exist(['S_201101_extn_blmrbl_{}.png'.format(version)])

    def test_creates_daily_conc_blue_marble_image_north(self):
        self.run_command('-h N --concentration --blue_marble --daily -y 2011 -m 1 --flatten'
                         ' -d 12 -o {}'.format(self.output_dir))
        self.assert_files_exist(['N_20110112_conc_blmrbl_{}.png'.format(version)])

    def test_creates_monthly_conc_blue_marble_image_south(self):
        self.run_command('-h S --concentration --blue_marble --monthly -y 2011 -m 1 --flatten'
                         ' -o {}'.format(self.output_dir))
        self.assert_files_exist(['S_201101_conc_blmrbl_{}.png'.format(version)])

    def test_creates_monthly_extent_google_image(self):
        options_str = '-y {year} -m {month} -o {output}'.format(year=2011,
                                                                month=1,
                                                                output=self.output_dir)

        self.runner.invoke(sii_image_google_earth, options_str.split(' '), catch_exceptions=False)

        self.assert_files_exist(['201101_extn_google_{}_goddard.png'.format(version)])

    def test_creates_science_on_a_sphere_image(self):
        start = '2016-09-01'
        end = '2016-09-07'
        days = 7
        options_str = '-s {start} -e {end} -d {days} -o {output}'.format(start=start,
                                                                         end=end,
                                                                         days=days,
                                                                         output=self.output_dir)
        self.runner.invoke(sii_image_sos, options_str.split(' '), catch_exceptions=False)

        filename = 'nt_monthext_20160901-20160907_f17_sos.png'
        self.assert_files_exist([filename])

        full_filename = os.path.join(self.output_dir, filename)
        run('convert -scale 20% {0} {0}'.format(full_filename), shell=True)

    def test_creates_extent_geotiff_image(self):
        options_str = '-h N --monthly --extent --flatten '\
                      '-y {year} -m {month} -o {output}'.format(year=2011,
                                                                month=1,
                                                                output=self.output_dir)
        self.runner.invoke(sii_image_geotiff, options_str.split(' '),
                           catch_exceptions=False)

        self.assert_files_exist(['N_201101_extent_{}.tif'.format(version)])

    def test_creates_conc_geotiff_image(self):
        options_str = '-h S --daily --concentration --flatten -d {day} '\
                      '-y {year} -m {month} -o {output}'.format(year=2011,
                                                                month=1,
                                                                day=1,
                                                                output=self.output_dir)
        self.runner.invoke(sii_image_geotiff, options_str.split(' '),
                           catch_exceptions=False)

        self.assert_files_exist(['S_20110101_concentration_{}.tif'.format(version)])
