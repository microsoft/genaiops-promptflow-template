pipeline {
    agent any
    
    parameters {
        string(name: 'azure_credentials', description: 'service principal auth to Azure', defaultValue: '', trim: true)
    }
    
    stages {
        stage('Azure Login') {
            steps {
                script {
                    // Azure login
                    azureLogin(azureCredentialsId: params.azure_credentials)
                }
            }
        }
    }
}
