pipeline {
  agent any

  stages {

    stage('Clone Code') {
      steps {
        git 'https://github.com/jeevamani007/jenkins_project.git'
      }
    }

    stage('Logic Check') {
      steps {
        script {
          if (env.BRANCH_NAME == 'main') {
            echo 'Main branch detected'
          } else {
            echo 'Not main branch'
          }
        }
      }
    }

    stage('Build Test') {
      steps {
        echo 'Jenkins pipeline working'
      }
    }
  }

  post {
    success {
      echo 'Pipeline executed successfully'
    }
    failure {
      echo 'Pipeline failed'
    }
  }
}
