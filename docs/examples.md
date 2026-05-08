# Examples

## Basic Usage
To score your Facebook data and output the CSVs into a directory called `results`:

```bash
fb-network-scorer /path/to/facebook-export --output ./results
```

## Running the Doctor
If you aren't sure if your export format is correct, you can run the diagnostic tool. The `doctor` command safely verifies directory structure and file presence without scanning any message contents.

```bash
fb-network-scorer doctor /path/to/facebook-export
```

## Synthetic Data
This repository includes a fake, synthetic data sample. You can test the scorer by running:

```bash
fb-network-scorer examples/sample_export --output ./examples/sample_output
```
