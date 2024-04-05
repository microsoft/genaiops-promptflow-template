def call(String requirements_type) {
    withPythonEnv('/usr/bin/python3.9') {
    sh """
    pip install setuptools wheel
    pip install -r .jenkins/requirements/${requirements_type}.txt
    pip install promptflow promptflow-tools promptflow-sdk jinja2 promptflow[azure] openai promptflow-sdk[builtins]
    """
    }
}