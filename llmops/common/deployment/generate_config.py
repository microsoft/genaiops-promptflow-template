"""
This script reads flow file and extracts the 'init' element.

The init element is extracted from the 'sample' element.
It then generates a list of environment variables based on
the contents of the 'init' element.
The script expects the name of the YAML file as a command-line argument.
The script also expects a second command-line argument that specifies whether
the output should be formatted as environment variables or as a list of
command-line arguments.
"""
# Import the required libraries
import yaml
import json
import sys
import os
from dotenv import load_dotenv

# Get the file name from the command-line argument
file_name = sys.argv[1]

is_env = sys.argv[2]

load_dotenv()
# Read the YAML file
with open(file_name, 'r') as file:
    data = yaml.safe_load(file)

output_list = []
output = ""
model_config_dict = {}
if 'init' in data:
    init_data = data['init']

    # Create the output list
    # output_list = []
    # Iterate over the top-level elements under 'init'
    for key, value in init_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                inner_params = {}
                if isinstance(sub_value, dict):
                    for sub_sub_key, sub_sub_value in sub_value.items():
                        if (
                            isinstance(sub_sub_value, str)
                            and sub_sub_value.startswith('${')
                            and sub_sub_value.endswith('}')
                        ):
                            env_var_name = f"{key}_{sub_sub_key}"
                            env_var_value = os.environ.get(
                                env_var_name.upper()
                                )
                            if env_var_value:
                                env_value = env_var_value
                            else:
                                env_value = sub_sub_value
                        else:
                            env_value = sub_sub_value
                        inner_params[sub_sub_key] = env_value
                    model_config_dict[key] = inner_params
                elif isinstance(sub_value, str) and sub_key == 'type':
                    pass
                elif isinstance(sub_value, str):
                    env_value = ""
                    if sub_value.startswith('${') and sub_value.endswith('}'):
                        env_var_value = os.environ.get(key.upper())
                        if env_var_value:
                            env_value = env_var_value
                        else:
                            env_value = value
                    else:
                        env_value = sub_value
                    inner_params[key] = env_value
                    model_config_dict[key] = inner_params[key]
                elif isinstance(sub_value, int):
                    inner_params[key] = sub_value
                    model_config_dict[key] = inner_params[key]


# Extract the 'init' element from the YAML data
elif 'sample' in data and 'init' in data['sample']:
    init_data = data['sample']['init']

    # Create the output list
    # output_list = []
    # Iterate over the top-level elements under 'init'
    for key, value in init_data.items():
        if isinstance(value, dict):
            # Convert the sub-elements to a JSON string without spaces
            # sub_elements_json = json.dumps(value, separators=(',', ':'))
            inner_params = {}
            for sub_key, sub_value in value.items():
                if (
                    isinstance(sub_value, str)
                    and sub_value.startswith('${')
                    and sub_value.endswith('}')
                ):
                    env_var_name = f"{key}_{sub_key}"
                    env_var_value = os.environ.get(env_var_name.upper())
                    if env_var_value:
                        env_value = env_var_value
                    else:
                        env_value = sub_value
                else:
                    env_value = sub_value

                inner_params[sub_key] = env_value
            model_config_dict[key] = inner_params
        elif isinstance(value, str):
            if value.startswith('${') and value.endswith('}'):
                env_var_value = os.environ.get(key.upper())
                if env_var_value:
                    env_value = env_var_value
                else:
                    env_value = value
            model_config_dict[key.upper()] = value
        elif isinstance(value, int):
            model_config_dict[key.upper()] = value

    # Join the output list with spaces
else:
    output = ''

sub_elements_json = json.dumps(
    model_config_dict, separators=(',', ':')
)
if is_env == 'true':
    if sub_elements_json:
        output_list.append(
            f'-e PF_FLOW_INIT_CONFIG={sub_elements_json}'
        )
else:
    if sub_elements_json:
        output_list.append(f'PF_FLOW_INIT_CONFIG={sub_elements_json}')
# Print the output
output = ' '.join(output_list)
print(output)
