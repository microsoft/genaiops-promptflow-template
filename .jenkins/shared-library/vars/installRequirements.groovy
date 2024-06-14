def call(String requirements_type) {
    withPythonEnv('/usr/bin/python3.9') {
    sh """
    pip install setuptools wheel
    pip uninstall -y promptflow promptflow-core promptflow-devkit promptflow-azure
    pip install -r .jenkins/requirements/${requirements_type}.txt
    """
    }
}