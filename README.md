# Saturn Run - the cli tool for dispatching scripts over clusters.

## The Basics

### Run Configuration

A yaml file contains a few aspects of the run:

1. What execution engine is going to compute the results
2. Where are the logs and results going to be stored
3. Are there any code artifacts that should be synchronized between the client and the server.

One example:

```
executor:
  class_spec: DaskExecutor
  scheduler_address: tcp://127.0.0.1:8786
results:
  class_spec: LocalResults
  path: /tmp/results/{name}
```

Another example:

```
executor:
  class_spec: DaskExecutor
  cluster_class: SaturnCluster
results:
  class_spec: S3Results
  s3_url: s3://saturn-internal-s3-test/saturn-run-2022.12.13/{name}/
file_syncs:
  - src: /home/jovyan/workspace/julia-example/
```

### Task configuration

A yaml file containing the tasks to be computed:

One example:
```
tasks:
  - command: julia /home/jovyan/workspace/julia-example/fibonacci.jl 12
  - command: julia /home/jovyan/workspace/julia-example/fibonacci.jl 30
  - command: julia /home/jovyan/workspace/julia-example/fibonacci.jl 5
  - command: julia /home/jovyan/workspace/julia-example/fibonacci.jl 13
```

### Run Results

Run results are organized in directories by job. Each directory has stdout, stderr, status, and possibly results.

### Executing

To execute - just pass in the 2 yamls, along with the name of the run.

```
saturn run run.yaml tasks.yaml --name my-job
```

## Advanced Concepts

### Names

All runs have a name (which passed in to the CLI). You can also specify `--prefix` instead of name, which will generate a name using the `prefix` and the timestamp.

The individual jobs of a run also have names. If un-specified, we count from 0 and use that as the name.

### Reconnecting to a job

When a run is executed, it is dispatched to the cluster, and then the individual jobs are monitored. This process of monitoring and waiting for jobs to complete is called `collect`. If we kick off a run, and we hit ctrl-c before the job completes, we can re-connect to it with `saturn collect`

```
$ saturn collect run.yaml --name my-job
```

Note - that `tasks.yaml` is not needed to collect, but `run.yaml` is. This is because the state is often stored on the cluster, and `run.yaml` is what defines the cluster. In addition, if names were generated via `--prefix`, you will need the generated name in order
to collect.

Whenever possible, `saturn run` is architected to make collecting un-necessary. However some configurations we may have in the future ( for example collecting results from a cluster to local disk ) will require the collection process.

## Future Work

The long term goal of this project is to support many different cluster types.

Example cluster types:

- Saturn Job Cluster
- Ray Cluster
- multiprocessing

