@description('The type of the environment')
param environmentType string
@description('The name of the key vault to be created.')
param vaultName string = 'kv-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('Location for all resources.')
param location string = resourceGroup().location
@description('The SKU of the vault to be created.')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'
@description('The name of the key vault pep to be created.')
param vaultPepName string = 'pep-kv-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('The Subnet ID where the Key Vault Private Link is to be created')
param subnetId string
@description('The VNet ID where the Key Vault Private Link is to be created')
param virtualNetworkId string
@description('Enable Network Isolation for the Key Vault')
param enableNetworkIsolation bool

@description('Associated private SSH key to connect to the Linux VM')
@secure()
param sshPrivateKey string


resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: vaultName
  location: location
  properties: {    
    accessPolicies: []
    createMode: 'default'
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: null
    enabledForDeployment: true
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    tenantId: subscription().tenantId
    publicNetworkAccess: (enableNetworkIsolation ? 'Disabled' : null)
    sku: {
      name: skuName
      family: 'A'
    }
    networkAcls: {
      defaultAction: (!enableNetworkIsolation ? 'Allow' : 'Deny')
      bypass: 'AzureServices'
    }
  }
}

resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2022-01-01' = if (enableNetworkIsolation) {
  name: vaultPepName
  location: location
  properties: {
    privateLinkServiceConnections: [
      {
        name: vaultPepName
        properties: {
          groupIds: [
            'vault'
          ]
          privateLinkServiceId: keyVault.id
        }
      }
    ]
    subnet: {
      id: subnetId
    }
  }
}

resource keyVaultPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enableNetworkIsolation) {
  name: 'privatelink.vaultcore.azure.net'
  location: 'global'
}

resource privateEndpointDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-01-01' = if (enableNetworkIsolation) {
  name: 'vault-PrivateDnsZoneGroup'
  parent: keyVaultPrivateEndpoint
  properties:{
    privateDnsZoneConfigs: [
      {
        name: keyVaultPrivateDnsZone.name
        properties:{
          privateDnsZoneId: keyVaultPrivateDnsZone.id
        }
      }
    ]
  }
}

resource keyVaultPrivateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enableNetworkIsolation) {
  name: uniqueString(keyVault.id)
  parent: keyVaultPrivateDnsZone
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetworkId
    }
  }
}


resource sshLinuxPrivateKey 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = if (enableNetworkIsolation) {
  name: 'ssh-private-key-linux'
  parent: keyVault
  properties: {
    value: sshPrivateKey
  }
}



output keyVaultDnsZoneName string = keyVaultPrivateDnsZone.name
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
