#!/usr/bin/env python3

import argparse
import logging
import json
import yaml
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigLegacyFeatureDeprecator:
    """
    Identifies and flags deprecated features or configuration parameters within config files.
    """

    def __init__(self, config_file, config_type, deprecated_features_file):
        """
        Initializes the ConfigLegacyFeatureDeprecator.

        Args:
            config_file (str): Path to the configuration file.
            config_type (str): Type of configuration file (e.g., 'yaml', 'json').
            deprecated_features_file (str): Path to the JSON file containing deprecated features.
        """
        self.config_file = config_file
        self.config_type = config_type.lower()
        self.deprecated_features_file = deprecated_features_file
        self.config_load_failed = False
        self.config_empty = False
        self.features_load_failed = False
        # Both files are loaded here, in the constructor, before run
        # gets any say. Constructing this object is therefore an IO
        # operation, and the flags set by the loaders are the only
        # record of what went wrong until run reads them.
        self.deprecated_features = self.load_deprecated_features()
        self.config_data = self.load_config_data()


    def load_config_data(self):
        """
        Loads the configuration data from the specified file.

        Returns:
            dict: The configuration data as a dictionary.
            None: If the file does not exist or if loading fails.
        """
        if not os.path.exists(self.config_file):
            logging.error(f"Configuration file not found: {self.config_file}")
            self.config_load_failed = True
            return None

        try:
            with open(self.config_file, 'r') as f:
                if self.config_type == 'yaml':
                    # The parser comes from the required type flag, never from
                    # the file name. Declaring a JSON document as yaml succeeds,
                    # because YAML reads JSON, while declaring YAML as json fails
                    # in the loader and is reported as a load failure.
                    data = yaml.safe_load(f)
                elif self.config_type == 'json':
                    data = json.load(f)
                else:
                    logging.error(f"Unsupported configuration type: {self.config_type}")
                    self.config_load_failed = True
                    return None
            if data is None:
                self.config_empty = True
            return data
        except Exception as e:
            logging.error(f"Error loading configuration file: {e}")
            self.config_load_failed = True
            return None


    def load_deprecated_features(self):
        """
        Loads the deprecated features from the specified JSON file.

        Returns:
            dict: A dictionary of deprecated features.
            None: If the file does not exist or loading fails.
        """
        if not os.path.exists(self.deprecated_features_file):
            logging.error(f"Deprecated features file not found: {self.deprecated_features_file}")
            self.features_load_failed = True
            return None

        try:
            with open(self.deprecated_features_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading deprecated features file: {e}")
            self.features_load_failed = True
            return None
    def find_deprecated_features(self, data, path=""):
        """
        Recursively searches for deprecated features within the configuration data.

        Args:
            data (dict or list): The configuration data to search.
            path (str): The path to the current data (used for nested structures).

        Returns:
            list: A list of deprecated features found in the configuration.
        """
        deprecated_found = []

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                # A name is all I match on, at any depth. The same word used
                # as an unrelated setting inside a newer section is flagged
                # as the deprecated feature, and a deprecated feature set to
                # false, switched off, is flagged exactly like a live one,
                # because the value is never looked at.
                if key in self.deprecated_features:
                    deprecated_found.append({
                        "feature": key,
                        "path": new_path,
                        "deprecation_info": self.deprecated_features[key]
                    })
                # I keep walking into a matched key's value, so a deprecated
                # feature whose own settings contain another deprecated name
                # produces both findings. The paths are the only way a reader
                # can tell the nested one sits inside the first.
                deprecated_found.extend(self.find_deprecated_features(value, new_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                deprecated_found.extend(self.find_deprecated_features(item, new_path))

        return deprecated_found

    def run(self):
        """
        Runs the deprecation checker.
        """
        if self.config_load_failed or self.features_load_failed:
            logging.error("Loading failed: the configuration or deprecated features file could not be loaded. Exiting.")
            return None
        if self.deprecated_features is not None and not isinstance(self.deprecated_features, dict):
            logging.error(f"Deprecated features file must hold a JSON object mapping feature names to details, got {type(self.deprecated_features).__name__}. Exiting.")
            return None
        if not self.deprecated_features:
            logging.error("Deprecated features file is empty. Nothing was checked. Exiting.")
            return None
        if self.config_empty or not self.config_data:
            logging.error("Configuration file is empty. Nothing was checked. Exiting.")
            return None

        # A config that parses to a plain scalar reaches this call and
        # finds nothing, because the search only understands mappings
        # and lists. run then returns an empty list and main exits 0,
        # a clean verdict for a file that held no checkable settings
        # at all, unlike an empty file, which the checks above refuse.
        deprecated_features_found = self.find_deprecated_features(self.config_data)

        if deprecated_features_found:
            logging.warning("Deprecated features found in the configuration file:")
            for feature in deprecated_features_found:
                logging.warning(f"  Feature: {feature['feature']}")
                logging.warning(f"  Path: {feature['path']}")
                logging.warning(f"  Details: {feature['deprecation_info']}")
                logging.warning("-" * 30)
        else:
            logging.info("No deprecated features found in the configuration file.")

        return deprecated_features_found


def setup_argparse():
    """
    Sets up the argument parser for the command line interface.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description='Identifies and flags deprecated features in configuration files.')
    parser.add_argument('--config-file', required=True, help='Path to the configuration file.')
    parser.add_argument('--config-type', required=True, choices=['yaml', 'json'], help='Type of the configuration file (yaml or json).')
    parser.add_argument('--deprecated-features-file', required=True, help='Path to the JSON file containing deprecated features.')
    return parser

def main():
    """
    Main function to execute the deprecation checker.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Input validation: Check if files exist
    if not os.path.exists(args.config_file):
        logging.error(f"Configuration file not found: {args.config_file}")
        sys.exit(1)  # Exit with an error code

    if not os.path.exists(args.deprecated_features_file):
        logging.error(f"Deprecated features file not found: {args.deprecated_features_file}")
        sys.exit(1)  # Exit with an error code

    deprecator = ConfigLegacyFeatureDeprecator(args.config_file, args.config_type, args.deprecated_features_file)
    deprecated_features = deprecator.run()

    if deprecated_features is None:
        sys.exit(1)  # Loading, empty input, or a wrongly typed features file
    if deprecated_features:
        # Two is a deliberate third state: 0 means checked and clean,
        # 1 means I could not check, and 2 means I checked and found.
        # A caller using the usual success or failure test reads 2
        # as failure, which is the safe direction, but a caller that
        # compares against 1 alone would miss the findings.
        sys.exit(2) # Exit with a code indicating deprecated features were found
    else:
        sys.exit(0) # Normal exit with no deprecated features

if __name__ == "__main__":
    # Example Usage:
    # Create a sample config file (test_config.yaml)
    # Create a sample deprecated features file (deprecated_features.json)
    # Run the script: python3 main.py --config-file test_config.yaml --config-type yaml --deprecated-features-file deprecated_features.json

    # Example Content for test_config.yaml:
    # api_version: v1
    # deprecated_feature: true
    # settings:
    #   old_setting: 123
    #   new_setting: 456

    # Example Content for deprecated_features.json:
    # {
    #   "deprecated_feature": {
    #     "description": "This feature is deprecated. Use new_feature instead.",
    #     "replacement": "new_feature"
    #   },
    #   "old_setting": {
    #     "description": "This setting is deprecated. Use new_setting instead.",
    #     "replacement": "new_setting"
    #   },
    #   "api_version": {
    #     "description": "API Version v1 is deprecated.",
    #     "replacement": "v2"
    #    }
    # }

    main()