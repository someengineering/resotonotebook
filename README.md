# resotonotebook
Small library for using Resoto with Jupyter Notebooks.

## Installation

```bash
pip install resotonotebook
```

## Usage

```python
from resotonotebook import ResotoNotebook
rnb = ResotoNotebook("https://localhost:8900", None)
rnb.search("is(instance)").groupby(["kind"])["kind"].count()
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
