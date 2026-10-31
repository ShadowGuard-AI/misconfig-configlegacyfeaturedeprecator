![Banner](banner.png)

# misconfig-ConfigLegacyFeatureDeprecator
Identifies and flags deprecated features or configuration parameters within config files, helping users migrate to newer configurations. - Focused on Check for misconfigurations in configuration files or infrastructure definitions

## Install
`git clone https://github.com/ShadowGuardAI/misconfig-configlegacyfeaturedeprecator`

## Usage
`python3 main.py --config-file config.yaml --config-type yaml --deprecated-features-file deprecated_features.json`

## Parameters
- `-h`: Show help message and exit
- `--config-file`: Path to the configuration file.
- `--config-type`: Type of the configuration file, yaml or json.

The deprecated features file must be a JSON object mapping feature names to their deprecation details. A run exits 2 when deprecated features are found, 0 when real content was checked and none were found, and 1 when a file fails to load, is empty, or the features file is not a JSON object.
- `--deprecated-features-file`: Path to the JSON file containing deprecated features.

## License
Copyright (c) ShadowGuardAI
