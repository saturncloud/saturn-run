# Saturn Run - the library for embarassingly parallel computations.

## The CLI

runs are submitted via YAML

```
$ saturn run run.yaml --name run1
```

Where `run.yaml` is the following:

```
name: lr-sweep
tasks:
  - name: lr-0.5
    command: python train.py --lr 0.5
  - name: lr-0.6
    command: python train.py --lr 0.6
  - name: lr-0.7
    command: python train.py --lr 0.7
  - name: lr-0.8
    command: python train.py --lr 0.8
executor:
  class_spec: DaskExecutor
  scheduler_address: "tcp://127.0.0.1:8886"
results:
  class_spec: LocalDir
  directory: /tmp/results
```

Results are collected (if necessary)

```
$ saturn collect --name lr-sweep
```

The cluster (and any running runs) can be terminated
```
$ saturn terminate --name lr-sweep
```

## Results - intermediate, and final

This section describes intermediate results (run state, as well as logs), and how the final output of runs are handled (whether they result in an success or failure).

The output structure of an saturn run looks like this:

```
- /tmp/results/lr-0.5/
  - log
  - events
  - status
  - results
- /tmp/results/lr-0.6/
  - log
  - events
  - status
  - results
- /tmp/results/lr-0.7/
  - log
  - events
  - status
  - error
- /tmp/results/lr-0.8/
  - log
  - events
  - status
  - results
```

* **log**: This is the stdout and stderr of user code, written to disk
* **events**: This is a yaml file describing the state of the run. It looks like this:
  ```
  events:
    - type: submitted
      utctimestamp: 2022-09-11T20:31:59.555695+00:00
    - type: complete
      utctimestamp: 2022-09-11T20:31:59.555695+00:00
  ```
* **error**: If there is an error, an exit code is written to "error"
* **status**: "success" or "failure", written after the run terminates.


## Examples of executor backends
- DaskBackend
- RayBackend
- RFuturesBackend
- MultiprocessingBackend
- KubernetesBackend


## Examples of results backends
User code is dispatched via the Python `subprocessing` module. Saturn run will monitor the process as it runs.

- LocalDir
  - Logs. When a run is executed, User code writes directly to stdout. Saturn-Run will periodically reads stdout/stderr, and write to the log file within LocalDir.
  - Results. A results directory is passed via an environment variable. User code writes to the results directory.
  - Status is written by saturn-run when the status is complete.
  - Error code is written by saturn-run when the run is complete.
- S3
  - Logs. When a run is executed, User code writes directoy to stdout. Saturn-Run will periodically read stdout/stderr, write them to local disk, and synchronize them to a directory in S3. Since you cannot append to a file in S3, saturn-run will organize log output into N minute chunks, and synchronize those files to S3.
- DaskBackend.
  - Logs. Logs are read by saturn-run and streamed back to the client via a Dask Queue. These are written to a local directory on the client machine during `collect`
  - Results. A results directory is passed via an environment variable. After data is written there. the contents are sent into a Dask Queue, and written to a local directory on the client machine during `collect`
