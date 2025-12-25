import yaml
import os

def load_config(config_path="config.yaml"):
    # Adjust path if running from a service subdirectory
    if not os.path.exists(config_path):
        # Try going up two levels (services/service_name/ -> root)
        config_path = "../../config.yaml"
        
    if not os.path.exists(config_path):
        # Try going up three levels (services/shared/ -> root)
        config_path = "../../../config.yaml"

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
