#!/bin/bash

# Description: 
# This script deploys prompt flow image to Public Azure Web App

# This is sample script to show the deployment process.
# Update it as necessary.

# Replace/Update the code here to provision webapps for
# private networks and/or use different means of provisioning
# using Terraform, Bicep or any other way.

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

set -e # fail on error

# read values from deployment_config.json related to `webapp_endpoint`
env_name=$deploy_environment
deploy_config="./$use_case_base_path/configs/deployment_config.json"
con_object=$(jq ".webapp_endpoint[] | select(.ENV_NAME == \"$env_name\")" "$deploy_config")
REGISTRY_NAME=$(echo "$con_object" | jq -r '.REGISTRY_NAME')
rgname=$(echo "$con_object" | jq -r '.WEB_APP_RG_NAME')
udmid=$(echo "$con_object" | jq -r '.USER_MANAGED_ID')
appserviceplan=$(echo "$con_object" | jq -r '.APP_PLAN_NAME')
appserviceweb=$(echo "$con_object" | jq -r '.WEB_APP_NAME')
acr_rg=$(echo "$con_object" | jq -r '.REGISTRY_RG_NAME')
websku=$(echo "$con_object" | jq -r '.WEB_APP_SKU')

read -r -a connection_names <<< "$(echo "$con_object" | jq -r '.CONNECTION_NAMES | join(" ")')"
echo $connection_names

# create a resource group
az group create --name $rgname --location westeurope

# create a user managed identifier      
az identity create --name $udmid --resource-group $rgname
sleep 15
      
principalId=$(az identity show --resource-group $rgname \
    --name $udmid --query principalId --output tsv)
      
registryId=$(az acr show --resource-group $acr_rg \
    --name $REGISTRY_NAME --query id --output tsv)

# provide permissions to user managed identifier      
az role assignment create --assignee $principalId --scope $registryId --role "AcrPull"
az appservice plan create --name $appserviceplan --resource-group $rgname --is-linux --sku $websku

# create/update Web App
az webapp create --resource-group $rgname --plan $appserviceplan --name $appserviceweb --deployment-container-image-name \
    $REGISTRY_NAME.azurecr.io/"$use_case_base_path"_"$deploy_environment":"$build_id"

# create/update Web App config settings
az webapp config appsettings set --resource-group $rgname --name $appserviceweb \
    --settings WEBSITES_PORT=8080

for name in "${connection_names[@]}"; do
    api_key=$(echo ${CONNECTION_DETAILS} | jq -r --arg name "$name" '.[] | select(.name == $name) | .api_key')

    uppercase_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
    modified_name="${uppercase_name}_API_KEY"
    az webapp config appsettings set \
        --resource-group $rgname \
        --name $appserviceweb \
        --settings $modified_name=$api_key
done

# Assign user managed identifier to Web APp
id=$(az identity show --resource-group $rgname --name $udmid --query id --output tsv)

az webapp identity assign --resource-group $rgname --name $appserviceweb --identities $id
 
appConfig=$(az webapp config show --resource-group $rgname --name $appserviceweb --query id --output tsv)

az resource update --ids $appConfig --set properties.acrUseManagedIdentityCreds=True

clientId=$(az identity show --resource-group $rgname --name $udmid --query clientId --output tsv)

az resource update --ids $appConfig --set properties.AcrUserManagedIdentityID=$clientId

