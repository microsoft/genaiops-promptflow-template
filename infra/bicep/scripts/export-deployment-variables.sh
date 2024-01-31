#!/bin/bash
repoRoot=$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../../../"
    pwd -P
)

# # shellcheck disable=SC2034
# while getopts "k:g:e:w:r:i:" opt; do
#     case $opt in
#     k) kvName=$OPTARG ;;
#     g) rgName=$OPTARG ;;  
#     e) envName=$OPTARG ;;      
#     w) workspaceName=$OPTARG ;;      
#     r) runtimeName=$OPTARG ;;      
#     i) networkIsolationBool=$OPTARG ;;      
#     :)
#         echo "Error: -${OPTARG} requires a value"
#         exit 1
#         ;;
#     *)
#         exit 1
#         ;;
#     esac
# done

# # The LLMOPS configJSON file
# FILE_LLMOPS="${repoRoot}/llmops_config.json"

# #If the llmops_config.json file does not exist, create it and add one block containing the environment variables
# if [[ ! -e $FILE_LLMOPS ]]; then
#     echo "File $FILE_LLMOPS does not exist, creating it..."
#     touch $FILE_LLMOPS
#     blockToAdd="{
#                     \"ENV_NAME\": \"$envName\",
#                     \"RUNTIME_NAME\": \"$runtimeName\",
#                     \"KEYVAULT_NAME\": \"$kvName\",
#                     \"RESOURCE_GROUP_NAME\": \"$rgName\",
#                     \"WORKSPACE_NAME\": \"$workspaceName\",
#                     \"STANDARD_FLOW_PATH\": \"flows/experiment\",
#                     \"EVALUATION_FLOW_PATH\": \"flows/evaluation, flows/evaluation_adv\"
#                 }"
#     echo "File $FILE_LLMOPS created."
#     cat << EOF > $FILE_LLMOPS
# {
#     "envs":[
#                 $blockToAdd
#             ]
# }
# EOF
# else
#     #If the the llmops_config.json exists, update it. 
#     #The update is done by adding a new block if the environment does not exist, or by updating the existing block if the environment already exists
#     echo "File $FILE_LLMOPS already exists. Updating configuration of environment $envName..."
#     jq --arg envName "$envName" --arg runtimeName "$runtimeName" --arg kvName "$kvName" --arg rgName "$rgName" --arg workspaceName "$workspaceName" '
#     if any(.envs[]; .ENV_NAME == $envName) then
#         .envs |= map(
#             if .ENV_NAME == $envName then
#                 .ENV_NAME = $envName
#                 | .RUNTIME_NAME = $runtimeName
#                 | .KEYVAULT_NAME = $kvName
#                 | .RESOURCE_GROUP_NAME = $rgName
#                 | .WORKSPACE_NAME = $workspaceName
#             else
#                 .
#             end
#         )
#     else
#         .envs += [
#             {
#                 "ENV_NAME": $envName,
#                 "RUNTIME_NAME": $runtimeName,
#                 "KEYVAULT_NAME": $kvName,
#                 "RESOURCE_GROUP_NAME": $rgName,
#                 "WORKSPACE_NAME": $workspaceName,
#                 "STANDARD_FLOW_PATH": "flows/experiment",
#                 "EVALUATION_FLOW_PATH": "flows/evaluation"
#             }
#         ]
#     end' $FILE_LLMOPS > temp.json && mv temp.json $FILE_LLMOPS
# fi

networkIsolationBool=true
# Now set "PUBLIC_ACCESS" to true in deployment_config.json
FILE_DEPLOYMENT="${repoRoot}/deployment_config.json"

#If the llmops_config.json file does not exist, create it and add one block containing the environment variables
if [[ ! -e $FILE_DEPLOYMENT ]]; then
    echo "File $FILE_DEPLOYMENT does not exist, creating it..."
    touch $FILE_DEPLOYMENT
    blockToAddDeployment="{
    \"azure_managed_endpoint\":[
        {
            \"ENV_NAME\": \"dev\",
            \"TEST_FILE_PATH\": \"sample-request.json\",
            \"PUBLIC_ACCESS\": \"$networkIsolationBool\",
            \"ENDPOINT_NAME\": \"\",
            \"ENDPOINT_DESC\": \"An online endpoint serving a flow for [task]\",
            \"DEPLOYMENT_DESC\": \"prompt flow deployment\",
            \"PRIOR_DEPLOYMENT_NAME\": \"\",
            \"PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION\": \"\",
            \"CURRENT_DEPLOYMENT_NAME\": \"\",
            \"CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION\": \"100\",
            \"DEPLOYMENT_VM_SIZE\": \"Standard_F4s_v2\",
            \"DEPLOYMENT_BASE_IMAGE_NAME\": \"mcr.microsoft.com/azureml/promptflow/promptflow-runtime:latest\",
            \"DEPLOYMENT_CONDA_PATH\": \"environment/conda.yml\",
            \"DEPLOYMENT_INSTANCE_COUNT\": 1,
            \"ENVIRONMENT_VARIABLES\": {
                \"example-name\": \"example-value\"
            }
        }
    ],
    \"kubernetes_endpoint\":[
        {
            \"ENV_NAME\": \"dev\",
            \"TEST_FILE_PATH\": \"sample-request.json\",
            \"PUBLIC_ACCESS\": \"$networkIsolationBool\",
            \"ENDPOINT_NAME\": \"\",
            \"ENDPOINT_DESC\": \"An kubernetes endpoint serving a flow for [task]\",
            \"DEPLOYMENT_DESC\": \"prompt flow deployment\",
            \"PRIOR_DEPLOYMENT_NAME\": \"\",
            \"PRIOR_DEPLOYMENT_TRAFFIC_ALLOCATION\": \"\",
            \"CURRENT_DEPLOYMENT_NAME\": \"\",
            \"CURRENT_DEPLOYMENT_TRAFFIC_ALLOCATION\": 100,
            \"COMPUTE_NAME\": \"\",
            \"DEPLOYMENT_VM_SIZE\": \"promptinstancetype\",
            \"DEPLOYMENT_BASE_IMAGE_NAME\": \"mcr.microsoft.com/azureml/promptflow/promptflow-runtime:latest\",
            \"DEPLOYMENT_CONDA_PATH\": \"environment/conda.yml\",
            \"DEPLOYMENT_INSTANCE_COUNT\": 1,
            \"CPU_ALLOCATION\": \"\",
            \"MEMORY_ALLOCATION\": \"\",
            \"ENVIRONMENT_VARIABLES\": {
                \"example-name\": \"example-value\"
            }
        }
    ]
}"
    echo "File $FILE_DEPLOYMENT created."
    cat << EOF > $FILE_DEPLOYMENT
    $blockToAddDeployment
EOF
else
    #If the the deployment_config.json.json exists, update it to set value of "PUBLIC_ACCESS" to true or false
    echo "File $FILE_DEPLOYMENT already exists. Updating it to set value of PUBLIC_ACCESS"
    # jq --arg networkIsolationBool "$networkIsolationBool" '.[] |= (.[] | .PUBLIC_ACCESS = "$networkIsolationBool")' $FILE_DEPLOYMENT > tempd.json && mv tempd.json $FILE_DEPLOYMENT
    jq --arg networkIsolationBool "$networkIsolationBool" ' .[].PUBLIC_ACCESS |= $networkIsolationBool ' $FILE_DEPLOYMENT > tempd.json && mv tempd.json $FILE_DEPLOYMENT
fi

