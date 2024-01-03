// Creates an Azure Container Registry with Azure Private Link endpoint
@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('Container registry name')
param nameContainerRegistry string

@description('Container registry private link endpoint name')
param nameContainerRegistryPep string

@description('Resource ID of the subnet')
param subnetId string

@description('Resource ID of the virtual network')
param virtualNetworkId string

@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool


var nameContainerRegistryCleaned = replace(nameContainerRegistry, '-', '')
var privateDnsZoneName = 'privatelink${environment().suffixes.acrLoginServer}'
var groupName = 'registry' 


resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: nameContainerRegistryCleaned
  location: location
  tags: tags
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: true
    dataEndpointEnabled: false
    networkRuleBypassOptions: 'AzureServices'
    networkRuleSet: {
      defaultAction: (!enableNetworkIsolation ? 'Allow' : 'Deny')
    }
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      retentionPolicy: {
        status: 'enabled'
        days: 7
      }
      trustPolicy: {
        status: 'disabled'
        type: 'Notary'
      }
    }
    publicNetworkAccess: (!enableNetworkIsolation ? 'Enabled' : 'Disabled')
    zoneRedundancy: 'Disabled'
  }
}

resource containerRegistryPrivateEndpoint 'Microsoft.Network/privateEndpoints@2022-01-01' = if (enableNetworkIsolation) {
  name: nameContainerRegistryPep
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      {
        name: nameContainerRegistryPep
        properties: {
          groupIds: [
            groupName
          ]
          privateLinkServiceId: containerRegistry.id
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource acrPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: privateDnsZoneName
  location: 'global'
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = if (enableNetworkIsolation) {
  name: '${groupName}-PrivateDnsZoneGroup'
  parent: containerRegistryPrivateEndpoint
  properties:{
    privateDnsZoneConfigs: [
      {
        name: privateDnsZoneName
        properties:{
          privateDnsZoneId: acrPrivateDnsZone.id
        }
      }
    ]
  }
}

resource acrPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(containerRegistry.id)
  parent: acrPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

output containerRegistryId string = containerRegistry.id
output nameContainerRegistry string = containerRegistry.name
