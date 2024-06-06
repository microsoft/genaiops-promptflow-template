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

# Extract the 'init' element from the YAML data
if 'sample' in data and 'init' in data['sample']:
    init_data = data['sample']['init']

    # Create the output list
    output_list = []
    model_config_dict = {}
    # Iterate over the top-level elements under 'init'
    for key, value in init_data.items():
        if isinstance(value, dict):
            # Convert the sub-elements to a JSON string without spaces
            # sub_elements_json = json.dumps(value, separators=(',', ':'))
            inner_params = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str) and sub_value.startswith('${') and sub_value.endswith('}'):
                    env_var_name = f"{key}_{sub_key}"
                    env_var_value = os.environ.get(env_var_name)
                    if env_var_value:
                        env_value = env_var_value
                    else:
                        env_value = "sub_value"
                else:
                    env_value = sub_value

                inner_params[sub_key] = env_value
            model_config_dict["model_config"] = inner_params
            sub_elements_json = json.dumps(model_config_dict, separators=(',', ':'))
            if is_env == 'true':
                output_list.append(f'-e PF_FLOW_INIT_CONFIG={sub_elements_json}')
            else:
                output_list.append(f'PF_FLOW_INIT_CONFIG={sub_elements_json}')
        elif isinstance(value, str):
            if value.startswith('${') and value.endswith('}'):
                env_var_value = os.environ.get(key)
                if env_var_value:
                    env_value = env_var_value
                else:
                    env_value = value

            if is_env == 'true':
                output_list.append(f'-e {key.upper()}={value}')
            else:
                output_list.append(f'{key.upper()}={value}')
        elif isinstance(value, int):
            if is_env == 'true':
                output_list.append(f'-e {key.upper()}={value}')
            else:
                output_list.append(f'{key.upper()}={value}')

    # Join the output list with spaces
    output = ' '.join(output_list)
else:
    output = ''

# Print the output
print(output)
