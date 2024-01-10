#!/bin/bash
repoRoot=$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../../../"
    pwd -P
)

# shellcheck disable=SC2034
while getopts "k:g:e:w:r:" opt; do
    case $opt in
    k) kvName=$OPTARG ;;
    g) rgName=$OPTARG ;;  
    e) envName=$OPTARG ;;      
    w) workspaceName=$OPTARG ;;      
    r) runtimeName=$OPTARG ;;      
    :)
        echo "Error: -${OPTARG} requires a value"
        exit 1
        ;;
    *)
        exit 1
        ;;
    esac
done

# The JSON file
FILE="${repoRoot}/llmops_config.json"

#If the llmops_config.json file does not exist, create it and add one block containing the environment variables
if [[ ! -e $FILE ]]; then
    echo "File $FILE does not exist, creating it..."
    touch $FILE
    blockToAdd="{
                    \"ENV_NAME\": \"$envName\",
                    \"RUNTIME_NAME\": \"$runtimeName\",
                    \"KEYVAULT_NAME\": \"$kvName\",
                    \"RESOURCE_GROUP_NAME\": \"$rgName\",
                    \"WORKSPACE_NAME\": \"$workspaceName\",
                    \"STANDARD_FLOW_PATH\": \"flows/experiment\",
                    \"EVALUATION_FLOW_PATH\": \"flows/evaluation, flows/evaluation_adv\"
                }"
    echo "File $FILE created."
    cat << EOF > $FILE
{
    "envs":[
                $blockToAdd
            ]
}
EOF
else
    #If the the llmops_config.json exists, update it. 
    #The update is done by adding a new block if the environment does not exist, or by updating the existing block if the environment already exists
    echo "File $FILE already exists. Updating it configuration of environment $envName..."
    jq --arg envName "$envName" --arg runtimeName "$runtimeName" --arg kvName "$kvName" --arg rgName "$rgName" --arg workspaceName "$workspaceName" '
    if any(.envs[]; .ENV_NAME == $envName) then
        .envs |= map(
            if .ENV_NAME == $envName then
                .ENV_NAME = $envName
                | .RUNTIME_NAME = $runtimeName
                | .KEYVAULT_NAME = $kvName
                | .RESOURCE_GROUP_NAME = $rgName
                | .WORKSPACE_NAME = $workspaceName
            else
                .
            end
        )
    else
        .envs += [
            {
                "ENV_NAME": $envName,
                "RUNTIME_NAME": $runtimeName,
                "KEYVAULT_NAME": $kvName,
                "RESOURCE_GROUP_NAME": $rgName,
                "WORKSPACE_NAME": $workspaceName,
                "STANDARD_FLOW_PATH": "flows/experiment",
                "EVALUATION_FLOW_PATH": "flows/evaluation"
            }
        ]
    end' $FILE > temp.json && mv temp.json $FILE
fi
