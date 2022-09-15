import logging

import click
from ruamel.yaml import YAML
from saturn_run.run import RunConfig


@click.group()
def cli():
    pass


@cli.command(help="executes a run from the definition in RUN_YAML")
@click.argument("run-yaml")
@click.option("--name")
@click.option("--prefix")
def run(run_yaml, name, prefix):
    logging.basicConfig(level=logging.INFO)
    with open(run_yaml, "r") as f:
        parsed = YAML().load(f)
    run_config = RunConfig.from_yaml(name=name, prefix=prefix, **parsed)
    run_config.run()


@cli.command(help="executes a run from the definition in RUN_YAML")
@click.argument("run-yaml")
@click.option("--name")
def collect(run_yaml, name):
    logging.basicConfig(level=logging.INFO)
    with open(run_yaml, "r") as f:
        parsed = YAML().load(f)
    run_config = RunConfig.from_yaml(name=name, **parsed)
    run_config.executor.collect(name)


if __name__ == "__main__":
    cli()
