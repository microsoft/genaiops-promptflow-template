@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('Name of the storage account')
param nameStorage string

@description('Name of the storage blob private link endpoint')
param nameStoragePleBlob string

@description('Name of the storage file private link endpoint')
param nameStoragePleFile string

@description('Resource ID of the subnet')
param subnetId string

@description('Resource ID of the virtual network')
param virtualNetworkId string

@allowed([
  'Standard_LRS'
  'Standard_ZRS'
  'Standard_GRS'
  'Standard_GZRS'
  'Standard_RAGRS'
  'Standard_RAGZRS'
  'Premium_LRS'
  'Premium_ZRS'
])
@description('Storage SKU')
param nameStorageSku string = 'Standard_LRS'

@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool

var nameStorageCleaned = replace(nameStorage, '-', '')
var nameBlobPrivateDnsZone = 'privatelink.blob.${environment().suffixes.storage}'
var nameFilePrivateDnsZone = 'privatelink.file.${environment().suffixes.storage}'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: nameStorageCleaned
  location: location
  tags: tags
  sku: {
    name: nameStorageSku
  }
  kind: 'StorageV2'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: (!enableNetworkIsolation ? true : false)
    publicNetworkAccess: (!enableNetworkIsolation ? 'Enabled' : 'Disabled')
    allowCrossTenantReplication: false
    allowSharedKeyAccess: true
    encryption: {
      keySource: 'Microsoft.Storage'
      requireInfrastructureEncryption: false
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
        queue: {
          enabled: true
          keyType: 'Service'
        }
        table: {
          enabled: true
          keyType: 'Service'
        }
      }
    }
    isHnsEnabled: false
    isNfsV3Enabled: false
    keyPolicy: {
      keyExpirationPeriodInDays: 7
    }
    largeFileSharesState: 'Disabled'
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: (!enableNetworkIsolation ? 'Allow' : 'Deny')
    }
    supportsHttpsTrafficOnly: true
  }
}

resource storagePrivateEndpointBlob 'Microsoft.Network/privateEndpoints@2022-01-01' = if (enableNetworkIsolation) {
  name: nameStoragePleBlob
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      { 
        name: nameStoragePleBlob
        properties: {
          groupIds: [
            'blob'
          ]
          privateLinkServiceId: storage.id
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-Approved'
            actionsRequired: 'None'
          }
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource storagePrivateEndpointFile 'Microsoft.Network/privateEndpoints@2022-01-01' = if (enableNetworkIsolation) {
  name: nameStoragePleFile
  location: location
  tags: tags
  properties: {
    privateLinkServiceConnections: [
      {
        name: nameStoragePleFile
        properties: {
          groupIds: [
            'file'
          ]
          privateLinkServiceId: storage.id
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-Approved'
            actionsRequired: 'None'
          }
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource blobPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: nameBlobPrivateDnsZone
  location: 'global'
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = if (enableNetworkIsolation) {
  name: 'blob-PrivateDnsZoneGroup'
  parent: storagePrivateEndpointBlob
  properties:{
    privateDnsZoneConfigs: [
      {
        name: nameBlobPrivateDnsZone
        properties:{
          privateDnsZoneId: blobPrivateDnsZone.id
        }
      }
    ]
  }
}


resource blobPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(storage.id)
  parent: blobPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

resource filePrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: nameFilePrivateDnsZone
  location: 'global'
}

resource filePrivateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = if (enableNetworkIsolation) {
  name: 'flie-PrivateDnsZoneGroup'
  parent: storagePrivateEndpointFile
  properties:{
    privateDnsZoneConfigs: [
      {
        name: nameFilePrivateDnsZone
        properties:{
          privateDnsZoneId: filePrivateDnsZone.id
        }
      }
    ]
  }
}

resource filePrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(storage.id)
  parent: filePrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}

output storageId string = storage.id
output nameStorage string = storage.name
