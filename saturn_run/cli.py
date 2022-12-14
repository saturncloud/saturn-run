import logging

logging.basicConfig(level=logging.INFO)

import click  # noqa
from ruamel.yaml import YAML  # noqa
from saturn_run.run import RunConfig, TaskConfig  # noqa


@click.group()
def cli():
    pass


@cli.command(help="executes a run from the definition in RUN_YAML")
@click.argument("run-yaml")
@click.argument("task-yaml")
@click.option("--name", default=None)
@click.option("--prefix", default=None)
def run(run_yaml, task_yaml, name, prefix):
    logging.basicConfig(level=logging.INFO)
    with open(run_yaml, "r") as f:
        parsed = YAML().load(f)
    run_config = RunConfig.from_yaml(name=name, prefix=prefix, **parsed)
    if prefix and name:
        raise ValueError('prefix and name are mutually exclusive')
    if prefix:
        run_config.executor.cleanup(prefix)
    else:
        run_config.executor.cleanup(name)
    with open(task_yaml, "r") as f:
        parsed = YAML().load(f)
    tasks = TaskConfig.from_yaml(**parsed)

    run_config.run(tasks)
    run_config.executor.collect(run_config.name)


@cli.command(help="executes a run from the definition in RUN_YAML")
@click.argument("run-yaml")
@click.option("--name")
def collect(run_yaml, name):
    with open(run_yaml, "r") as f:
        parsed = YAML().load(f)
    run_config = RunConfig.from_yaml(name=name, **parsed)
    run_config.executor.collect(name)


if __name__ == "__main__":
    cli()
