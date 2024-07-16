"""
This script reads a YAML file and generates a list of environment variables.

The script expects the name of the YAML file as a command-line argument.
The script also expects a second command-line argument that specifies whether
the output should be formatted as environment variables or as a list of
command-line arguments.
"""
# Import the required libraries
import yaml
import sys
import os
from dotenv import load_dotenv

load_dotenv()
# Get the file name from the command-line argument
file_name = sys.argv[1]

is_env = sys.argv[2]

# Read the YAML file
with open(file_name, 'r') as file:
    data = yaml.safe_load(file)

# Extract the 'init' element from the YAML data

# Create the output list
output_list = []

# Iterate over the top-level elements under 'init'
for key, value in data.items():
    key = str(key).strip()
    value = str(value).strip()
    if value.startswith('${') and value.endswith('}'):
        value = value.replace('${', '').replace('}', '')
        resolved_value = os.environ.get(value.upper(), None)
        if resolved_value is None:
            raise ValueError(
                f"Environment variable {value.upper()} not found"
            )
    else:
        resolved_value = value

    if is_env == 'true':
        output_list.append(
            f'-e {key.upper()}={resolved_value}'
        )
    else:
        output_list.append(
            f'{key.upper()}={resolved_value}'
        )

# Join the output list with spaces
output = ' '.join(output_list)

# Print the output
print(output)
