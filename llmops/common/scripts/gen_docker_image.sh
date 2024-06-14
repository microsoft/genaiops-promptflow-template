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
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done
source .env
# Use the assigned variables as needed
echo "Flow to execute: $use_case_base_path"
echo "Deploy environment: $deploy_environment"
echo "Build ID: $build_id"

# Description: 
# This script generates docker image for Prompt flow deployment
set -e # fail on error

# read values from experiment.yaml related to given environment
config_path="./$use_case_base_path/experiment.yaml"
env_var_file_path="./$use_case_base_path/environment/env.yaml"

##remove
cat "$config_path"
##remove

source .env
. .env
if [[ -e "$config_path" ]]; then
    STANDARD_FLOW=$(yq eval '.flow // .name' "$config_path")

    init_file_path="./$use_case_base_path/$STANDARD_FLOW/flow.flex.yaml"

    init_output=""
    if [ -e "$init_file_path" ]; then
        init_output=$(python llmops/common/deployment/generate_config.py "$init_file_path" "true")
    fi
    echo "$init_output"

    env_output=""
    if [ -e "$env_var_file_path" ]; then
        env_output=$(python llmops/common/deployment/generate_env_vars.py "$env_var_file_path" "true")
    fi
    echo "$env_output"
 

    pip install -r ./$use_case_base_path/$STANDARD_FLOW/requirements.txt
    pf flow build --source "./$use_case_base_path/$STANDARD_FLOW" --output "./$use_case_base_path/docker"  --format docker 

    cp "./$use_case_base_path/environment/Dockerfile" "./$use_case_base_path/docker/Dockerfile"
   
    python -m llmops.common.deployment.migrate_connections --base_path $use_case_base_path --env_name $deploy_environment
    # docker build the prompt flow based image
    docker build --platform=linux/amd64 -t localpf "./$use_case_base_path/docker" 
        
    docker images

    deploy_config="./$use_case_base_path/configs/deployment_config.json"
    con_object=$(jq ".webapp_endpoint[] | select(.ENV_NAME == \"$deploy_environment\")" "$deploy_config")

    read -r -a connection_names <<< "$(echo "$con_object" | jq -r '.CONNECTION_NAMES | join(" ")')"
    result_string=""
    printenv
    for name in "${connection_names[@]}"; do
        uppercase_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
        env_var_key="${uppercase_name}_API_KEY"
        api_key=${!env_var_key}
        result_string+=$(printf " -e %s=%s" "$env_var_key" "$api_key")
    done
    echo "$result_string"
    docker_args=$result_string

    if [ -n "$init_output" ]; then
        docker_args+=" $init_output"
    fi

    if [ -n "$env_output" ]; then
        docker_args+=" $env_output"
    fi
    
    docker_args+=" -m 512m --memory-reservation=256m --cpus=2 -dp 8080:8080 localpf:latest"
    echo "$docker_args"

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