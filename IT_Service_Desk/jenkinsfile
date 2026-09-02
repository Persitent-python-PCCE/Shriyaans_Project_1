pipeline {
    agent any

    stages {

        stage('Checkout'){
            steps{
                checkout scm
            }
        }

        stage('Install Dependencies'){
            steps{
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test'){
            steps {
                sh 'pytest'
            }
        }

        stage('Build Docker Image'){
            steps{
                sh 'docker build -t arulguru03/flask-app:latest'
            }
        }

        stage('Push to Docker Hub') {
            steps{
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-cred',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )
                ]){
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push arulguru03/flask-app:latest
                    '''
                }
            }
        }

    }

}