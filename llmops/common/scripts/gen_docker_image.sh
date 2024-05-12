#!/bin/bash

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --use_case_base_path)
            use_case_base_path="$2"
            shift 2
            ;;
        --deploy_environment)
            deploy_environment="$2"
            shift 2
            ;;
        --build_id)
            build_id="$2"
            shift 2
            ;;
        --REGISTRY_DETAILS)
            REGISTRY_DETAILS="$2"
            shift 2
            ;;
        --CONNECTION_DETAILS)
            CONNECTION_DETAILS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Use the assigned variables as needed
echo "Flow to execute: $use_case_base_path"
echo "Deploy environment: $deploy_environment"
echo "Build ID: $build_id"

# Description: 
# This script generates docker image for Prompt flow deployment
set -e # fail on error

# read values from experiment.yaml related to given environment
config_path="./$use_case_base_path/experiment.yaml"

if [[ -e "$config_path" ]]; then
    STANDARD_FLOW=$(yq eval '.flow // .name' "$config_path")

    pip install -r ./$use_case_base_path/$STANDARD_FLOW/requirements.txt
    pf flow build --source "./$use_case_base_path/$STANDARD_FLOW" --output "./$use_case_base_path/docker"  --format docker 

    # cp "./$use_case_base_path/environment/run" "./$use_case_base_path/docker/runit/promptflow-serve/run"
    cp "./$use_case_base_path/environment/Dockerfile" "./$use_case_base_path/docker/Dockerfile"

    # docker build the prompt flow based image
    docker build -t localpf "./$use_case_base_path/docker" --no-cache
        
    docker images

    deploy_config="./$use_case_base_path/configs/deployment_config.json"
    con_object=$(jq ".webapp_endpoint[] | select(.ENV_NAME == \"$deploy_environment\")" "$deploy_config")

    read -r -a connection_names <<< "$(echo "$con_object" | jq -r '.CONNECTION_NAMES | join(" ")')"
    result_string=""

    for name in "${connection_names[@]}"; do
        api_key=$(echo ${CONNECTION_DETAILS} | jq -r --arg name "$name" '.[] | select(.name == $name) | .api_key')
        uppercase_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        modified_name="${uppercase_name}_API_KEY"
        result_string+=" -e $modified_name=$api_key"
    done
    
    echo $CONNECTION_DETAILS
    echo $result_string

    docker_args=$result_string

    docker_args+=" -m 512m --memory-reservation=256m --cpus=2 -dp 8080:8080 localpf:latest"
    echo $docker_args
    docker run $(echo "$docker_args")

    sleep 15

    docker ps -a

    chmod +x "./$use_case_base_path/sample-request.json"

    file_contents=$(<./$use_case_base_path/sample-request.json)
    echo "$file_contents"

    python -m llmops.common.deployment.test_local_flow \
            --base_path $use_case_base_path

    registry_name=$(echo "${REGISTRY_DETAILS}" | jq -r '.[0].registry_name')
    registry_server=$(echo "${REGISTRY_DETAILS}" | jq -r '.[0].registry_server')
    registry_username=$(echo "${REGISTRY_DETAILS}" | jq -r '.[0].registry_username')
    registry_password=$(echo "${REGISTRY_DETAILS}" | jq -r '.[0].registry_password')

    docker login "$registry_server" -u "$registry_username" --password-stdin <<< "$registry_password"
    docker tag localpf "$registry_server"/"$use_case_base_path"_"$deploy_environment":"$build_id"
    docker push "$registry_server"/"$use_case_base_path"_"$deploy_environment":"$build_id"

else
    echo $config_path "not found"
fi
