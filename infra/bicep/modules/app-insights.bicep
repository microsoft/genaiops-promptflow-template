@description('The type of the environment')
param environmentType string
@description('Application Insight name')
param appInsightsName string = 'appinsights-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('Application Insight name')
param logAnalyticsWorkspaceName string = 'loganalyticsw-${environmentType}-${uniqueString(resourceGroup().id)}'
@description('Location for all resources.')
param location string = resourceGroup().location
@description('Enable public access to ease dev tests?')
param enableNetworkIsolation bool

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: ( enableNetworkIsolation ? 'Enabled' : 'Disabled' )
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    Flow_Type: 'Bluefield'
  }
}

output connectionString string = appInsights.properties.ConnectionString
output id string = appInsights.id
