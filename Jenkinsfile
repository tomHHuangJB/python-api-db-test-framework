pipeline {
    agent any

    environment {
        API_BASE_URL = "http://localhost:8000"
        API_KEY = "local-dev-key"
        DB_HOST = "localhost"
        DB_PORT = "5432"
        DB_NAME = "appdb"
        DB_USER = "appuser"
        DB_PASSWORD = "apppass"
        ALLURE_DIR = "allure-results"
        ALLURE_REPORT = "allure-report"
        SLACK_CHANNEL = "#localbuild"
        SLACK_TOKEN_CRED_ID = "slack-bot-token"
    }

    options {
        timestamps()
        ansiColor("xterm")
    }

    stages {
        stage("Checkout") {
            steps {
                checkout scm
            }
        }

        stage("Install Deps") {
            steps {
                sh """
                    python3.11 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements-dev.txt
                    python -m pip install -r perf/requirements.txt
                """
            }
        }

        stage("Start Services") {
            steps {
                sh "docker compose up -d --build"
            }
        }

        stage("Wait for API") {
            steps {
                sh """
                    for i in {1..30}; do
                      if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
                        exit 0
                      fi
                      sleep 2
                    done
                    echo "API did not become healthy in time"
                    exit 1
                """
            }
        }

        stage("Smoke Tests") {
            steps {
                sh ". .venv/bin/activate && python -m pytest -m smoke --junitxml=artifacts/junit-smoke.xml --alluredir=${ALLURE_DIR}-smoke"
            }
            post {
                always {
                    junit "artifacts/junit-smoke.xml"
                }
            }
        }

        stage("Full Tests") {
            steps {
                sh ". .venv/bin/activate && python -m pytest --junitxml=artifacts/junit.xml --alluredir=${ALLURE_DIR}"
            }
            post {
                always {
                    junit "artifacts/junit.xml"
                }
            }
        }

        stage("Lint & Typecheck") {
            steps {
                sh ". .venv/bin/activate && python -m ruff check ."
                sh ". .venv/bin/activate && python -m mypy api/app tests"
            }
        }

        stage("Generate Allure Report") {
            steps {
                sh """
                    if command -v allure >/dev/null 2>&1; then
                      allure generate ${ALLURE_DIR} -o ${ALLURE_REPORT} --clean
                    else
                      echo "Allure CLI not found; skipping report generation"
                    fi
                """
            }
        }

        stage("Performance Smoke") {
            steps {
                sh ". .venv/bin/activate && LOCUST_HOST=http://localhost:8000 python -m locust -f perf/locustfile.py --headless -u 10 -r 2 -t 10s --csv=artifacts/locust"
            }
        }
    }

    post {
        always {
            sh "docker compose down"
            archiveArtifacts artifacts: "artifacts/**, ${ALLURE_DIR}/**, ${ALLURE_REPORT}/**", allowEmptyArchive: true
        }

        success {
            emailext(
                subject: "SUCCESS: ${JOB_NAME} #${BUILD_NUMBER}",
                body: "Build succeeded. ${BUILD_URL}",
                to: "\${EMAIL_RECIPIENTS}"
            )
            slackSend(
                channel: "${SLACK_CHANNEL}",
                tokenCredentialId: "${SLACK_TOKEN_CRED_ID}",
                color: "good",
                message: "SUCCESS: ${JOB_NAME} #${BUILD_NUMBER} <${BUILD_URL}|Open>"
            )
        }

        failure {
            emailext(
                subject: "FAILURE: ${JOB_NAME} #${BUILD_NUMBER}",
                body: "Build failed. ${BUILD_URL}",
                to: "\${EMAIL_RECIPIENTS}"
            )
            slackSend(
                channel: "${SLACK_CHANNEL}",
                tokenCredentialId: "${SLACK_TOKEN_CRED_ID}",
                color: "danger",
                message: "FAILURE: ${JOB_NAME} #${BUILD_NUMBER} <${BUILD_URL}|Open>"
            )
        }
    }
}
