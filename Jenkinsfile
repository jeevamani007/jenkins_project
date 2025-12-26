pipeline {
    agent any

    environment {
        APP_NAME = "jenkins_project"
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "Code already checked out from SCM"
            }
        }

        stage('Logic Check') {
            steps {
                script {
                    echo "Running logic checks..."
                    // simple condition example
                    def status = "OK"
                    if (status == "OK") {
                        echo "Logic check passed"
                    } else {
                        error "Logic check failed"
                    }
                }
            }
        }

        stage('Build Test') {
            steps {
                echo "Build/Test stage running"
                // future use:
                // sh 'python --version'
                // sh 'pip install -r requirements.txt'
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline executed successfully"
        }
        failure {
            echo "❌ Pipeline failed"
        }
        always {
            echo "Pipeline finished"
        }
    }
}
