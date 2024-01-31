@description('Name of the Azure OpenAI resource')
param nameAOAI string

@description('The Azure Region to deploy the resources into')
param location string

@description('Name of the deployment that appears in the studio')
param nameDeploymentAOAI string

@description('Name of the model that will be deployed')
param nameDeployedModel string

@description('Version of the model that will be deployed')
param versionDeployedModel string

@description('SKU of the Azure OpenAI resource')
param skuAOAI object = {
  name: 'S0'
}

@description('Scale type of the Azure OpenAI resource')
param scaleTypeAOAI string = 'Standard'

@description('Environment type')
param environmentType string

@description('Azure OpenAI private link endpoint name')
param namePepAOAI string

@description('Resource ID of the subnet')
param subnetId string

@description('Resource ID of the virtual network')
param virtualNetworkId string

@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool

param privateDnsZoneName string

// Array containing the models we want to deploy
var deploymentsAOAI = [
  {
    name: nameDeploymentAOAI
    model: {
      format: 'OpenAI'
      name: nameDeployedModel
      version: versionDeployedModel
    }
    scaleSettings: {
      scaleType: scaleTypeAOAI
    }
  }
]

param tags object = {
  Creator: 'ServiceAccount'
  Service: 'OpenAI'
  Environment: environmentType
}


// Azure OpenAI service
resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: nameAOAI  
  location: location
  kind: 'OpenAI'
  properties: {
    publicNetworkAccess: (!enableNetworkIsolation ? 'Enabled' : 'Disabled')
    customSubDomainName: nameAOAI
    networkAcls: {
      defaultAction: (!enableNetworkIsolation ? 'Allow' : 'Deny')
    }
  }
  tags: tags
  sku: skuAOAI
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for deployment in deploymentsAOAI: {
  parent: azureOpenAI
  sku: {
    name: 'Standard'
    capacity: 120
  }
  name: deployment.name
  properties: {
    model: deployment.model
  }
}]



resource azureOpenAIPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-02-01' = if (enableNetworkIsolation) {
  name: namePepAOAI
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      {
        name: namePepAOAI
        properties: {
          groupIds: [
            'account'
          ]
          privateLinkServiceId: azureOpenAI.id
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource azureOpenAIPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: privateDnsZoneName
  location: 'global'
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-02-01' = if (enableNetworkIsolation) {
  name: 'openai-PrivateDnsZoneGroup'
  parent: azureOpenAIPrivateEndpoint
  properties:{
    privateDnsZoneConfigs: [
      {
        name: privateDnsZoneName
        properties:{
          privateDnsZoneId: azureOpenAIPrivateDnsZone.id
        }
      }
    ]
  }
}

resource azureAOAIPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(azureOpenAI.id)
  parent: azureOpenAIPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

output azureOpenAIId string = azureOpenAI.id
output azureOpenAIName string = azureOpenAI.name
