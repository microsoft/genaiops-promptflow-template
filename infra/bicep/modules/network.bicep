@description('The type of the environment')
param environmentType string
@description('Location for all resources.')
param location string = resourceGroup().location
@description('Name of the virtual network')
param vnetName string = 'vnet-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('llmops  subnet name')
param llmopsSubnetName string = 'snet-llmops-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('Name of the subnet where the Linux VM for SSH tunelling will be deployed')
param jumpboxSubnetName string = 'snet-jumpb-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('Address space for the virtual network')
param vnetAddressSpace string = '10.1.0.0/16'
@description('llmops subnet address prefix')
param llmopsSubnet string = '10.1.4.0/24'
@description('Jumpbox subnet address prefix')
param jumpboxSubnet string = '10.1.6.0/24'
@description('Group ID of the network security group')
param idNetworkSecurityGroup string
@description('Enable network isolation for the virtual network')
param enableNetworkIsolation bool


var subnetLlmops = [   
  { 
    name: llmopsSubnetName
    properties: {
      addressPrefix: llmopsSubnet
      privateEndpointNetworkPolicies: 'Disabled'
      privateLinkServiceNetworkPolicies: 'Disabled'
      networkSecurityGroup: {
        id: idNetworkSecurityGroup
      }
    }
  }
]

var subnetJumpbox = [
  {
    name: jumpboxSubnetName
    properties: {
      addressPrefix: jumpboxSubnet
    }
  }
]

var subnets = (enableNetworkIsolation ? concat(subnetLlmops, subnetJumpbox) : subnetLlmops)

resource vnet 'Microsoft.Network/virtualNetworks@2023-04-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressSpace
      ]
    }
    subnets: subnets
  }
}


output vnetId string = vnet.id
output llmopsSubnetId string = '${vnet.id}/subnets/${llmopsSubnetName}'
output jumpboxSubnetId string = '${vnet.id}/subnets/${jumpboxSubnetName}'


