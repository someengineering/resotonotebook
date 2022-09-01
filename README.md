# resotonotebook
Small library for using Resoto with Jupyter Notebooks.

## Installation into an existing environment

```bash
pip install resotonotebook
```

## Installation from scratch

```
# create a new venv
python3 -m venv venv --prompt "resotonotebook"
# use the created venv
source venv/bin/activate
# install all dependencies to run jupyter lab with resoto notebooks
pip install jupyterlab resotonotebook
# start jupyter labs: this will open a browser window
jupyter lab
```

## Usage

```python
from resotonotebook import ResotoNotebook
rnb = ResotoNotebook("https://localhost:8900", None)
await rnb.search("is(instance)").groupby(["kind"])["kind"].count()
```
```
kind
aws_ec2_instance        497
digitalocean_droplet      7
example_instance          2
gcp_instance             12
Name: kind, dtype: int64
```

For more see the notebook in the examples directory.
