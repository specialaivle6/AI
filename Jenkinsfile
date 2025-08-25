pipeline {
    agent any
    
    environment {
        ECR_REGISTRY = '307946665510.dkr.ecr.ap-northeast-2.amazonaws.com'
        ECR_REPOSITORY = 'solar-panel-ai'
        AWS_DEFAULT_REGION = 'ap-northeast-2'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DATE_TAG = sh(script: "date +%Y%m%d", returnStdout: true).trim()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                script {
                    docker.build("${ECR_REPOSITORY}:${IMAGE_TAG}")
                }
            }
        }
        
        stage('Login to ECR') {
            steps {
                echo 'Logging in to ECR...'
                withCredentials([usernamePassword(credentialsId: 'aws-ecr-credentials', 
                                                usernameVariable: 'AWS_ACCESS_KEY_ID', 
                                                passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | \
                        docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    '''
                }
            }
        }
        
        stage('Tag and Push Image') {
            steps {
                echo 'Tagging and pushing images...'
                sh '''
                    # 날짜 태그
                    docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:ai-${DATE_TAG}.${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:ai-${DATE_TAG}.${IMAGE_TAG}
                    
                    # latest 태그
                    docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                    docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                '''
            }
        }
        
        stage('Deploy to AI Server') {
            steps {
                echo 'Deploying to AI server...'
                sshagent(credentials: ['ai-server-ssh']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no ubuntu@10.0.3.76 '
                            cd /home/ubuntu/ai-service &&
                            docker compose pull &&
                            docker compose up -d --force-recreate &&
                            docker compose ps
                        '
                    '''
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Performing health check...'
                script {
                    // 30초 대기 후 헬스체크
                    sleep 30
                    
                    def healthCheckResult = sh(
                        script: 'curl -f http://10.0.3.76:8000/ || exit 1',
                        returnStatus: true
                    )
                    
                    if (healthCheckResult != 0) {
                        error 'Health check failed!'
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            // Slack 알림 (선택사항)
            // slackSend(message: "✅ AI 서비스 배포 성공: ${env.JOB_NAME} - ${env.BUILD_NUMBER}")
        }
        failure {
            echo 'Pipeline failed!'
            // slackSend(message: "❌ AI 서비스 배포 실패: ${env.JOB_NAME} - ${env.BUILD_NUMBER}")
        }
        always {
            // 빌드 후 정리
            sh 'docker system prune -f'
        }
    }
}
