// Creates a machine learning workspace, private endpoints and DNS zones for the azure machine learning workspace

@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('Machine learning workspace name')
param nameMachineLearning string

@description('Machine learning workspace display name')
param nameMachineLearningFriendly string = nameMachineLearning

@description('Machine learning workspace description')
param descriptionMachineLearning string

@description('Resource ID of the application insights resource')
param applicationInsightsId string

@description('Resource ID of the container registry resource')
param containerRegistryId string

@description('Resource ID of the key vault resource')
param keyVaultId string

@description('Resource ID of the storage account resource')
param storageAccountId string

@description('Resource ID of the Azure OpenAI  resource')
param azureOpenAIId string

@description('Resource ID of the subnet resource')
param subnetId string

@description('Resource ID of the virtual network')
param virtualNetworkId string

@description('Machine learning workspace private link endpoint name')
param machineLearningPepName string

@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool

var privateDnsZoneName =  'privatelink.api.azureml.ms'
var privateAznbDnsZoneName = 'privatelink.notebooks.azure.net'

resource machineLearning 'Microsoft.MachineLearningServices/workspaces@2023-10-01' = {
  name: nameMachineLearning
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    // workspace organization
    friendlyName: nameMachineLearningFriendly
    description: descriptionMachineLearning

    // dependent resources
    applicationInsights: applicationInsightsId
    containerRegistry: containerRegistryId
    keyVault: keyVaultId
    storageAccount: storageAccountId

    // Managed VNET
    managedNetwork: (enableNetworkIsolation ? {
      isolationMode: 'AllowInternetOutbound'
      outboundRules: {
        ruleAMLtoAOAI:{
          type:'PrivateEndpoint'
          destination: {
            serviceResourceId: azureOpenAIId
            subresourceTarget: 'account'
            sparkEnabled: false
            sparkStatus: 'Inactive'
            }
        }
      }
      status: {
        sparkReady: false
        status: 'active'
      }
    } : null)
    publicNetworkAccess: (!enableNetworkIsolation ? 'Enabled' : 'Disabled')
  }
}

resource machineLearningPrivateEndpoint 'Microsoft.Network/privateEndpoints@2022-01-01' = if (enableNetworkIsolation) {
  name: machineLearningPepName
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      {
        name: machineLearningPepName
        properties: {
          groupIds: [
            'amlworkspace'
          ]
          privateLinkServiceId: machineLearning.id
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource amlPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: privateDnsZoneName
  location: 'global'
}

resource amlPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(machineLearning.id)
  parent: amlPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

// Notebook
resource notebookPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: privateAznbDnsZoneName
  location: 'global'
}

resource notebookPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(machineLearning.id)
  parent: notebookPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = if (enableNetworkIsolation) {
  name: 'amlworkspace-PrivateDnsZoneGroup'
  parent: machineLearningPrivateEndpoint
  properties:{
    privateDnsZoneConfigs: [
      {
        name: privateDnsZoneName
        properties:{
          privateDnsZoneId: amlPrivateDnsZone.id
        }
      }
      {
        name: privateAznbDnsZoneName
        properties:{
          privateDnsZoneId: notebookPrivateDnsZone.id
        }
      }
    ]
  }
}

output nameMachineLearning string = machineLearning.name
output machineLearningId string = machineLearning.id
output machineLearningPrincipalId string = machineLearning.identity.principalId
output usedSuffix string = uniqueString(resourceGroup().id)
