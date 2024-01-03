// Creates a Data Science Virtual Machine jumpbox.
@description('Azure region of the deployment')
param location string = resourceGroup().location

@description('Resource ID of the subnet')
param subnetId string

@description('Network Security Group Resource ID')
param networkSecurityGroupId string

@description('Virtual machine admin username')
param adminUsername string

@description('Public SSH key to connect to the Linux VM')
param sshKey string


@description('Name of the Linux VM')
param nameVm string='VMsshLinux'


@description('Size of the Linux VM')
param vmSize string='Standard_DS1_v2'

var setSshKey = !empty(sshKey) // True if a non-empty string is provided
var dnsLabelPrefix=toLower('${nameVm}-${uniqueString(resourceGroup().id)}')
var publicIPAddressName = '${nameVm}PublicIP'
var osDiskType = 'Standard_LRS'
var nameNic='${nameVm}-nic'

resource networkInterface 'Microsoft.Network/networkInterfaces@2022-07-01' = {
  name: nameNic
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: subnetId
          }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIPAddress.id
          }
        }
      }
    ]
    networkSecurityGroup: {
      id: networkSecurityGroupId
    }
  }
}


resource publicSshKey 'Microsoft.Compute/sshPublicKeys@2022-11-01' = if (!empty(sshKey)) {
  name: 'sshkey-linuxmachine'
  location: location
  properties: {
    publicKey: sshKey
  }
}

var linuxConfiguration = {
  disablePasswordAuthentication: true
}
var linuxConfigurationWithSSH = {
  disablePasswordAuthentication: true
  ssh: {
    publicKeys: [
      {
        path: '/home/${adminUsername}/.ssh/authorized_keys'
        keyData: publicSshKey.properties.publicKey
      }
    ]
  }
}


resource publicIPAddress 'Microsoft.Network/publicIPAddresses@2023-02-01' = {
  name: publicIPAddressName
  location: location
  sku:{
      name:'Basic'
  }
  properties:{
      publicIPAllocationMethod:'Dynamic'
      dnsSettings:{
          domainNameLabel:dnsLabelPrefix
      }
      idleTimeoutInMinutes :4
   }
}

resource vm 'Microsoft.Compute/virtualMachines@2023-03-01' = {
  name: nameVm
  location: location
  properties:{
      hardwareProfile:{
          vmSize : vmSize
      }
      storageProfile:{
          osDisk:{
              createOption:'FromImage'
              managedDisk:{
                  storageAccountType : osDiskType 
              } 
          } 
          imageReference: {
            publisher: 'Canonical'
            offer: '0001-com-ubuntu-server-focal'
            sku: '20_04-lts-gen2'
            version: 'latest'
          }
      } 
      networkProfile:{
          networkInterfaces:[
              { 
                  id : networkInterface.id 
              } 
          ] 
      } 
      osProfile:{
          computerName : nameVm 
          adminUsername : adminUsername 
          linuxConfiguration : (setSshKey ? linuxConfigurationWithSSH : linuxConfiguration) 
      } 
   } 
}

output vmId string = vm.id
