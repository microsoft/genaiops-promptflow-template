def call(String requirements_type) {
    withPythonEnv('/usr/bin/python3.9') {
    sh """
    pip install setuptools wheel
    pip install -r .jenkins/requirements/${requirements_type}.txt
    pip uninstall -y promptflow promptflow-core promptflow-devkit promptflow-azure
    pip install promptflow>=1.11.0 promptflow-tools promptflow-sdk jinja2 promptflow[azure]>=1.11.0 openai promptflow-sdk[builtins]
    """
    }
}