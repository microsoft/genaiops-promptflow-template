
#!/bin/bash
env_name='dev'
deploy_config="./named_entity_recognition/configs/deployment_config.json"
con_object=$(jq ".webapp_endpoint[] | select(.ENV_NAME == \"$env_name\")" "$deploy_config")
CONNECTION_DETAILS='[{"name": "aoai","type": "azure_open_ai","api_base": "https://qweqeqweqwe/","api_key": "xxxxxxxxxxxx","api_type": "azure","api_version": "2023-03-15-preview"},{"name": "abra","type": "azure_open_ai","api_base": "https://asdasdwqedsfsdfsdf/","api_key": "xxxxxxxxxxxx","api_type": "azure","api_version": "2023-03-15-preview"}]'
connection_names=($(echo "$con_object" | jq -r '.CONNECTION_NAMES[]'))
constant=' -e '
result_string=""
secret_con=$(echo "$CONNECTION_DETAILS") 
echo $connection_names

for name in "${connection_names[@]}"; do
    api_key=$(echo $secret_con | jq -r --arg name "$name" '.[] | select(.name == $name) | .api_key')
    uppercase_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
    modified_name=${uppercase_name}_API_KEY
    result_string+=" -e $modified_name=$api_key"
done
#result_string="$constant$result_string"
echo $result_string

docker_args=$result_string
docker_args+=" -m 512m --memory-reservation=256m --cpus=2 -dp 8080:8080 localpf:latest"
docker run $($docker_args)