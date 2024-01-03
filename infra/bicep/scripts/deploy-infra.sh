#Bash shell
#Remaining TODO:
##Call create or update SP
## Pass sp secrets on as env vars to the bicep 
## Add the secrets in the keyvault

#!/bin/bash
repoRoot=$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../../"
    pwd -P
)
##############################################################################
# colors for formatting the output
##############################################################################
# shellcheck disable=SC2034
{
YELLOW='\033[1;33m'
GREEN='\033[1;32m'
RED='\033[0;31m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color
}
##############################################################################
#- print functions
##############################################################################
function printMessage(){
    echo -e "${GREEN}$1${NC}" 
}
function printWarning(){
    echo -e "${YELLOW}$1${NC}" 
}
function printError(){
    echo -e "${RED}$1${NC}" 
}
function printProgress(){
    echo -e "${BLUE}$1${NC}" 
}
##############################################################################
#- checkLoginAndSubscription 
##############################################################################
function checkLoginAndSubscription() {
    az account show -o none
    # shellcheck disable=SC2181
    if [ $? -ne 0 ]; then
        printError "\nYou seems disconnected from Azure, stopping the script."
        exit 1
    fi
}
##############################################################################
#- function used to check whether an error occurred
##############################################################################
function checkError() {
    # shellcheck disable=SC2181
    if [ $? -ne 0 ]; then
        echo -e "${RED}\nAn error occurred exiting from the current bash${NC}"
        exit 1
    fi
}
#######################################################
#- function used to print out script usage
#######################################################
function usage() {
    echo
    echo "Arguments:"
    echo -e " -e  [ENV] set environment where ENV=DEV, QA, PREPROD or PROD"
    echo -e " -r  [RESOURCE_GROUP] set resource group"

    echo
    echo "Example:"
    echo -e " bash ./deploy-infra.sh -e DEV -r DevRessourceGroup "
    echo -e " bash ./deploy-infra.sh -e QA -r QARessourceGroup "
    echo -e " bash ./deploy-infra.sh -e PREPROD -r PREPRODRessourceGroup"    
}

set -a # automatically export all variables
source "$repoRoot/config/.env" 2> /dev/null || true
set +a

NETWORK_ISOLATION=false
# shellcheck disable=SC2034
while getopts "e:r:i:" opt; do
    case $opt in
    e) TYPE_ENVIRONMENT=$OPTARG ;;
    r) RESOURCE_GROUP=$OPTARG ;;  
    i) NETWORK_ISOLATION=$OPTARG ;;      
    :)
        printError "Error: -${OPTARG} requires a value"
        exit 1
        ;;
    *)
        usage
        exit 1
        ;;
    esac
done

# Validation
if [[ -z "${TYPE_ENVIRONMENT}" || -z "${RESOURCE_GROUP}" ]]; then
    printError "Required parameters are missing"
    usage
    exit 1
fi

if [[ -z "$appId" || -z $password || -z $tenantId || -z $subId ]]; then
    printWarning "Variables \$appId \$password \$tenantId \$subId not set"
    printProgress "Interactive Azure login..."
    if [[ -z $tenantId ]]; then
        az login
    else
        az login -t $tenantId
    fi  
    if [[ ! -z $subId ]]; then
        az account set -s $subId
    fi     
else
    printProgress "Service Principal Azure login..."
    az login --service-principal -u $appId -p $password -t $tenantId
    az account set -s $subId
fi
checkLoginAndSubscription

printProgress "Installing jq..."
if [ "${OSTYPE}" == "msys" ]; then
    curl -s -L -o /usr/bin/jq.exe https://github.com/stedolan/jq/releases/latest/download/jq-win64.exe 
else
    sudo apt-get -y install  jq
fi

printProgress "Adding ml extension if not installed..."
az extension add --name "ml"

printProgress "Getting Resource Group Name..."
resourceGroupName=$(az group show -g "${RESOURCE_GROUP}" 2> /dev/null | jq '.name' | tr -d '"' ) || true
if [[ -z $resourceGroupName ]]; then
    printError "Resource Group ${RESOURCE_GROUP} doesn't exist"
    exit 1
fi     
printProgress "Resource Group Name: ${resourceGroupName}"

# Deploy the infrastructure for DEV environment

pathToBicep="${repoRoot}/bicep/main.bicep"
environmentType="${TYPE_ENVIRONMENT}"
networkIsolationBool=${NETWORK_ISOLATION}

printProgress "generate keys for the jumpbox..."

printProgress "Check if ssh keys already created in resource group ${resourceGroupName}..."
sshKeyName=$(az sshkey list -g "$resourceGroupName" --query "[?contains(name, 'sshkey-linuxmachine')].name" -o tsv)

if [ -z "$sshKeyName" ] || [ "$sshKeyName" == "" ];  then
    printProgress "Creating ssh keys in resource group ${resourceGroupName}..."
    yes y | ssh-keygen -t rsa -N "" -f /tmp/deploy_id_rsa
    privateSshKey=$(cat /tmp/deploy_id_rsa)
    publicSshKey=$(cat /tmp/deploy_id_rsa.pub)
    rm /tmp/deploy_id_rsa*
    printProgress "publicSshKey=$publicSshKey"
    printProgress "privateSshKey=$privateSshKey"
else
    printProgress "Ssh keys already created in resource group ${resourceGroupName}..."
    publicSshKey=""
    privateSshKey=""
fi

echo "networkIsolationBool=$networkIsolationBool"
echo "environmentType=$environmentType"
echo "resourceGroupName=$resourceGroupName"

# # printProgress "Deploying resources in resource group ${resourceGroupName}..."
az deployment group create --mode Incremental --resource-group $resourceGroupName --template-file $pathToBicep  --parameters environmentType=$environmentType keyVaultSku='standard' jumpboxSshKey="$publicSshKey" jumpboxSshPrivateKey="$privateSshKey" enableNetworkIsolation=$networkIsolationBool

if [ $networkIsolationBool = true ]; then
    printMessage "Getting AML Workspace name deployed in ${resourceGroupName} ..."

    nameAmlWorkspace=$(az deployment group show --resource-group ${resourceGroupName} --name azuremlWorkspace --query properties.outputs.nameMachineLearning.value -o tsv)
    usedSuffix=$(az deployment group show --resource-group ${resourceGroupName} --name azuremlWorkspace --query properties.outputs.usedSuffix.value -o tsv)
    nameStorageAccount=$(az deployment group show --resource-group ${resourceGroupName} --name storageMlops --query properties.outputs.nameStorage.value -o tsv)


    if [ -z "$nameAmlWorkspace" ];  then
        printProgress "Missing AML workspace name"
        printProgress "AML workspace name: ${nameAmlWorkspace}"
        exit 1
    fi

    printProgress "AML workspace name: ${nameAmlWorkspace}"

    if [ -z "$usedSuffix"  ];  then
        printProgress "Missing suffix, unable to create a managed compute instance for AML workspace"
        printProgress "Suffix: ${usedSuffix}"
        exit 1
    fi
    printProgress "Used suffix: ${usedSuffix}"

    printProgress "Provisionning AML managed VNET..."
    az ml workspace provision-network --name ${nameAmlWorkspace} -g ${resourceGroupName}
fi

checkError
printMessage "Deployment in resource group ${resourceGroupName} successful!"
