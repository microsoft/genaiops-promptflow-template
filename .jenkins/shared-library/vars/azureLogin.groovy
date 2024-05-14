def call() {
    withCredentials([azureServicePrincipal('AZURE_CREDENTIALS')]) {
        sh 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET -t $AZURE_TENANT_ID'
        sh 'az account set -s $AZURE_SUBSCRIPTION_ID'
    }
}