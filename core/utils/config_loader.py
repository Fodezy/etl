# etl/core/utils/config_loader.py

import yaml
from pathlib import Path
from typing import Dict, Any

# Define custom exceptions for clear error handling from this module.
class ConfigNotFoundError(Exception):
    """Raised when a connector's config.yaml file cannot be found."""
    pass

class ConfigFormatError(Exception):
    """Raised when a config.yaml file has a syntax error or is empty."""
    pass


def load_config(school_name: str) -> Dict[str, Any]:
    """
    Finds and loads a school's configuration file from the connectors directory.

    This function constructs the path to the expected config file based on the
    school's name, handles potential errors like a missing file or malformed
    YAML, and returns the configuration as a Python dictionary.

    Args:
        school_name: The identifier of the school, which must match the
                     directory name in `connectors/` (e.g., 'uog').

    Returns:
        A dictionary containing the parsed YAML configuration.

    Raises:
        ConfigNotFoundError: If the configuration file does not exist at the
                             expected location.
        ConfigFormatError: If the YAML file is improperly formatted or empty.
    """
    # Construct the path to the config file relative to the project root.
    # Assumes this file is at core/utils/config_loader.py
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "connectors" / school_name / "extract" / "config.yaml"

    if not config_path.is_file():
        raise ConfigNotFoundError(
            f"Configuration file not found for school '{school_name}'. "
            f"Expected location: {config_path}"
        )

    try:
        # Open with read permission and specified encoding
        with open(config_path, 'r', encoding='utf-8') as f:
            # Use safe_load to prevent arbitrary code execution
            config_data = yaml.safe_load(f)
            if not config_data:
                raise ConfigFormatError(f"Configuration file for '{school_name}' is empty.")
    except yaml.YAMLError as e:
        # Catch errors during YAML parsing (e.g., bad indentation)
        raise ConfigFormatError(
            f"Error parsing YAML file for school '{school_name}'. "
            f"Please check syntax. Details: {e}"
        ) from e
    
    return config_data

# Example block for quick, direct testing of this module
if __name__ == '__main__':
    print("--- Testing config_loader.py ---")
    # To test this, you must have a file at: etl/connectors/uog/config.yaml
    try:
        print("Attempting to load 'uog' config...")
        uog_config = load_config('uog')
        print("Successfully loaded 'uog' config!")
        print(f"School Name: {uog_config.get('school_name')}")
    except (ConfigNotFoundError, ConfigFormatError) as e:
        print(f"ERROR: {e}")
        
    print("\nAttempting to load non-existent 'xyz' config...")
    try:
        xyz_config = load_config('xyz')
    except (ConfigNotFoundError, ConfigFormatError) as e:
        print(f"Successfully caught expected error: {e}")