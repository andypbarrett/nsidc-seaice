# helper Class for validating year ranges in click.
import click


class YearRange(click.ParamType):
    name = 'YearRange'

    def convert(self, value, param, ctx):
        try:
            return tuple(sorted(int(year) for year in value.split(',')))
        except Exception as e:
            self.fail('Failure parsing {}. {}'.format(value, e))
