import logging

import click
from ruamel.yaml import YAML
from saturn_run.run import RunConfig, TaskConfig


@click.group()
def cli():
    pass


@cli.command(help="executes a run from the definition in RUN_YAML")
@click.argument("run-yaml")
@click.argument("task-yaml")
@click.option("--name")
@click.option("--prefix")
def run(run_yaml, task_yaml, name, prefix):
    logging.basicConfig(level=logging.INFO)
    with open(run_yaml, "r") as f:
        parsed = YAML().load(f)
    run_config = RunConfig.from_yaml(name=name, prefix=prefix, **parsed)

    with open(task_yaml, "r") as f:
        parsed = YAML().load(f)
    tasks = TaskConfig.from_yaml(**parsed)

    run_config.run(tasks)
    run_config.executor.collect(run_config.name)


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
