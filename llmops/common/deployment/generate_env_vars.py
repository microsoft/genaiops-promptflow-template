import yaml
import json
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
    if is_env == 'true':
        output_list.append(f'-e {key.upper()}={os.environ.get(key, None)}')
    else:
        output_list.append(f'{key.upper()}={os.environ.get(key, None)}')

    # Join the output list with spaces
if is_env == 'true':
    output = ' '.join(output_list)
else:
    output =  ' '.join(output_list)


# Print the output
print(output)