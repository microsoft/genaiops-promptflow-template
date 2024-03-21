#!/bin/bash

# Description: 
# This script generates docker image for Prompt flow deployment

set -e # fail on error

# read values from llmops_config.json related to given environment
echo "Flow details below:"
echo $flow_to_execute
echo $deploy_environment
echo $build_id
config_path="./$flow_to_execute/llmops_config.json"
env_name=$deploy_environment
selected_object=$(jq ".envs[] | select(.ENV_NAME == \"$env_name\")" "$config_path")

if [[ -n "$selected_object" ]]; then
    STANDARD_FLOW=$(echo "$selected_object" | jq -r '.STANDARD_FLOW_PATH')
        
    pf flow build --source "./$flow_to_execute/$STANDARD_FLOW" --output "./$flow_to_execute/docker"  --format docker 

    cp "./$flow_to_execute/environment/Dockerfile" "./$flow_to_execute/docker/Dockerfile"

    # docker build the prompt flow based image
    docker build -t localpf "./$flow_to_execute/docker" --no-cache
        
    docker images

    deploy_config="./$flow_to_execute/configs/deployment_config.json"
    con_object=$(jq ".webapp_endpoint[] | select(.ENV_NAME == \"$env_name\")" "$deploy_config")

    read -r -a connection_names <<< "$(echo "$con_object" | jq -r '.CONNECTION_NAMES | join(" ")')"
    echo $connection_names
    result_string=""

    for name in "${connection_names[@]}"; do
        api_key=$(echo $CONNECTION_DETAILS | jq -r --arg name "$name" '.[] | select(.name == $name) | .api_key')
        uppercase_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        modified_name="${uppercase_name}_API_KEY"
        result_string+=" -e $modified_name=$api_key"
    done

    docker_args=$result_string
    docker_args+=" -m 512m --memory-reservation=256m --cpus=2 -dp 8080:8080 localpf:latest"
    #docker run $(echo "$docker_args")

    #sleep 15

    #docker ps -a
        
    #chmod +x "./$flow_to_execute/sample-request.json"
        
    #file_contents=$(<./$flow_to_execute/sample-request.json)
    #echo "$file_contents"
        
    #python -m llmops.common.deployment.test_local_flow \
            #--flow_to_execute $flow_to_execute

    #echo
    echo "registry details"
    echo "$con_object" | jq -r '.REGISTRY_NAME'
    echo "$registry_object" | jq -r '.registry_server'
    echo "$registry_object" | jq -r '.registry_username'


    REGISTRY_NAME=$(echo "$con_object" | jq -r '.REGISTRY_NAME')

    registry_object=$(echo $REGISTRY_DETAILS | jq -r --arg name "$REGISTRY_NAME" '.[] | select(.registry_name == $name)')
    registry_server=$(echo "$registry_object" | jq -r '.registry_server')
    registry_username=$(echo "$registry_object" | jq -r '.registry_username')
    registry_password=$(echo "$registry_object" | jq -r '.registry_password')


    docker login "$registry_server" -u "$registry_username" --password-stdin <<< "$registry_password" 
    docker tag localpf "$registry_server"/"$flow_to_execute"_"$deploy_environment":$build_id
    docker push "$registry_server"/"$flow_to_execute"_"$deploy_environment":$build_id
        
    else
        echo "Object in config file not found"
    fi
