@description('Location for all resources.')
param location string = resourceGroup().location

@description('Type of environment (dev, qa, prod, ...).')
param environmentType string

@description('The SKU for Key Vault.')
param keyVaultSku string = 'premium'

@description('Public SSH key to connect to the Linux jumpbox')
param jumpboxSshKey string

@description('Associated private SSH key to connect to the Linux jumpbox')
param jumpboxSshPrivateKey string

@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool = false

@description('Set of tags to apply to all resources.')
param tags object = {
  environmentType: environmentType
}
// Parameters for the storage account
param storageSku string ='Standard_LRS'

module nsg 'modules/nsg.bicep' = {
  name: 'nsg-${uniqueString(resourceGroup().id)}'
  params: {
    location: location
    tags: tags 
    nameNsg: 'nsg-${uniqueString(resourceGroup().id)}'
  }
}

module network 'modules/network.bicep' = {
  name: 'vnet'
  params: {
    location: location
    environmentType: environmentType
    idNetworkSecurityGroup: nsg.outputs.networkSecurityGroup
    vnetName: 'vnet-${uniqueString(resourceGroup().id)}'
    vnetAddressSpace: '10.1.0.0/16'
    llmopsSubnet: '10.1.4.0/24'
    jumpboxSubnet: '10.1.6.0/24'
    enableNetworkIsolation: enableNetworkIsolation
  }
}

module appInsights 'modules/app-insights.bicep' = {
  name: 'appInsights'
  params: {
    location: location
    environmentType: environmentType
    enableNetworkIsolation: enableNetworkIsolation
  }
}


module keyVault 'modules/key-vault.bicep' = {
  name: 'keyVault'
  params: {
    location: location
    environmentType: environmentType
    skuName: keyVaultSku
    enableNetworkIsolation: enableNetworkIsolation
    sshPrivateKey: jumpboxSshPrivateKey
    virtualNetworkId: network.outputs.vnetId
    subnetId: network.outputs.llmopsSubnetId
  }
}



// Creating two storage accounts:
// - one for the Azure Machine Learning workspace
module storage 'modules/storage.bicep' = {
  name: 'storagellmops'
  params: {
    location: location
    nameStorage: 'stllmops${uniqueString(resourceGroup().id)}'
    nameStoragePleBlob: 'pep-blob-stllmops${uniqueString(resourceGroup().id)}'
    nameStoragePleFile: 'pep-file-stllmops${uniqueString(resourceGroup().id)}'
    nameStorageSku: storageSku
    subnetId: network.outputs.llmopsSubnetId
    virtualNetworkId: network.outputs.vnetId
    enableNetworkIsolation: enableNetworkIsolation
    tags: tags
  }
}


// Creating the Azure Container registry required by 
// Azure machine Learning to serve as a model registry
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'llmopsContainerRegistry'
  params: {
    location: location
    nameContainerRegistry: 'acr${uniqueString(resourceGroup().id)}'
    nameContainerRegistryPep: 'pep-acr-${uniqueString(resourceGroup().id)}'
    subnetId: network.outputs.llmopsSubnetId
    virtualNetworkId: network.outputs.vnetId
    enableNetworkIsolation: enableNetworkIsolation 
    tags: tags
  }
}


// Creating the Azure Machine Learning workspace, compute and networking resources
module azuremlWorkspace 'modules/machine-learning-workspace.bicep' = {
  name: 'azuremlWorkspace'
  params: {
    // workspace organization
    nameMachineLearning: 'amlws-${environmentType}-${uniqueString(resourceGroup().id)}'
    nameMachineLearningFriendly: 'Azure ML ${environmentType} workspace'
    descriptionMachineLearning: 'This is an AML workspace for ${environmentType} environment'
    location: location
    tags: tags

    // dependant resources
    applicationInsightsId: appInsights.outputs.id
    containerRegistryId: containerRegistry.outputs.containerRegistryId
    keyVaultId: keyVault.outputs.keyVaultId
    storageAccountId: storage.outputs.storageId
    azureOpenAIId: azureOpenAI.outputs.azureOpenAIId

    // networking
    subnetId: network.outputs.llmopsSubnetId
    virtualNetworkId: network.outputs.vnetId
    machineLearningPepName: 'pep-amlws-${uniqueString(resourceGroup().id)}'
    
    enableNetworkIsolation: enableNetworkIsolation
  }
  dependsOn: [
    keyVault
    containerRegistry
    appInsights
    storage
  ]
}

// Creating all the role assignments required for the end-to-end flow to work
module rolesAssignments 'modules/rolesAssignments.bicep' = {
  name: 'rolesAssignments-${uniqueString(resourceGroup().id)}'
  params: {
    nameStorage: storage.outputs.nameStorage
    azuremlWorkspacePrincipalId: azuremlWorkspace.outputs.machineLearningPrincipalId
  }
}

// Creating the Azure OpenAI resource
module azureOpenAI 'modules/azure-openai.bicep' = {
  name: 'azureOpenAI'
  params: {
    //Azure OpenAI resource
    nameAOAI: 'aoai-eastus-${environmentType}-${uniqueString(resourceGroup().id)}'
    location: location
    nameDeploymentAOAI: 'deployment-${environmentType}-gpt35-0301'
    nameDeployedModel: 'gpt-35-turbo'
    versionDeployedModel: '0301'
    skuAOAI: {
      name: 'S0'
    }
    environmentType: environmentType
    enableNetworkIsolation: enableNetworkIsolation

    // Networking
    subnetId: network.outputs.llmopsSubnetId
    virtualNetworkId: network.outputs.vnetId
    namePepAOAI: 'pep-aoai-eastus-${uniqueString(resourceGroup().id)}'
    privateDnsZoneName: 'privatelink.openai.azure.com'

  }
}


// Creating the SSH linux VM
module linuxmachine 'modules/linux-machine.bicep' = if (enableNetworkIsolation) {
  name: 'sshmachine'
  params: {
    location: location
    nameVm: 'VMsshLinux'
    subnetId: network.outputs.jumpboxSubnetId
    adminUsername: 'azureuser'
    sshKey: jumpboxSshKey
    networkSecurityGroupId: nsg.outputs.networkSecurityGroup
  }
}
