@description('Name of the storage account')
param nameStorage string

@description('AML workspace principal id')
param azuremlWorkspacePrincipalId string

// Identifiers for the required roles
var roleStorageTableDataContributorId = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
var roleFileDataPriviligedContributorId = '69566ab7-960f-475b-8e7c-b3118f30c6bd'


resource referenceStorage 'Microsoft.Storage/storageAccounts@2022-09-01' existing = {
  name: nameStorage
}


// Assign "Table data contributor" role to AML Workspace
resource roleAssignmentTableDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: referenceStorage
  name: guid(nameStorage, roleStorageTableDataContributorId, resourceGroup().id)
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', roleStorageTableDataContributorId)
    principalId: azuremlWorkspacePrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Assign "Storage File Data Privileged Contributor" role to AML Workspace
resource roleAssignmentFileDataPriviligedContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: referenceStorage
  name: guid(nameStorage, roleFileDataPriviligedContributorId, resourceGroup().id)
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', roleFileDataPriviligedContributorId)
    principalId: azuremlWorkspacePrincipalId
    principalType: 'ServicePrincipal'
  }
}
