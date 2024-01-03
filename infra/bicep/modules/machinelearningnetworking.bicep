// Creates private endpoints and DNS zones for the azure machine learning workspace
@description('Azure region of the deployment')
param location string

@description('Machine learning workspace private link endpoint name')
param nameMachineLearningPle string

@description('Resource ID of the virtual network resource')
param virtualNetworkId string

@description('Resource ID of the subnet resource')
param subnetId string

@description('Resource ID of the machine learning workspace')
param workspaceArmId string

@description('Tags to add to the resources')
param tags object

var privateDnsZoneName =  {
  azureusgovernment: 'privatelink.api.ml.azure.us'
  azurechinacloud: 'privatelink.api.ml.azure.cn'
  azurecloud: 'privatelink.api.azureml.ms'
}

var privateAznbDnsZoneName = {
    azureusgovernment: 'privatelink.notebooks.usgovcloudapi.net'
    azurechinacloud: 'privatelink.notebooks.chinacloudapi.cn'
    azurecloud: 'privatelink.notebooks.azure.net'
}

resource machineLearningPrivateEndpoint 'Microsoft.Network/privateEndpoints@2022-01-01' = {
  name: nameMachineLearningPle
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      {
        name: nameMachineLearningPle
        properties: {
          groupIds: [
            'amlworkspace'
          ]
          privateLinkServiceId: workspaceArmId
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource amlPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneName[toLower(environment().name)]
  location: 'global'
}

resource amlPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: uniqueString(workspaceArmId)
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
resource notebookPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateAznbDnsZoneName[toLower(environment().name)]
  location: 'global'
}

resource notebookPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: uniqueString(workspaceArmId)
  parent: notebookPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = {
  name: 'amlworkspace-PrivateDnsZoneGroup'
  parent: machineLearningPrivateEndpoint
  properties:{
    privateDnsZoneConfigs: [
      {
        name: privateDnsZoneName[environment().name]
        properties:{
          privateDnsZoneId: amlPrivateDnsZone.id
        }
      }
      {
        name: privateAznbDnsZoneName[environment().name]
        properties:{
          privateDnsZoneId: notebookPrivateDnsZone.id
        }
      }
    ]
  }
}
