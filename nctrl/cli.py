import click
from .core import NCtrl
from .unit import Unit

@click.group()
def main():
    pass

@main.command()
@click.option('--port', default=None, help='Serial port to use')
@click.option('--prbfile', default=None, help='Path to PRB file')
@click.option('--output', default='laser', help='Output type')
def bmi(port, prbfile, output):
    nctrl = NCtrl(prbfile=prbfile, output_port=port, output_type=output)
    nctrl.show()

@main.command()
@click.option('--file', default=None, help='Path to spktag model file')
@click.option('--id', default=None, help='Unit ID to simulate')
def unit(file, id):
    unit = Unit()
    unit.load(file)
    if id:
        unit.simulate(id)
    else:
        unit.plot()