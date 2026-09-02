PROJECT_ID=email-to-telegram-455900
REGION=us-central1

WATCH_TIME_ZONE=America/Phoenix
WATCH_SCHEDULE=0 6 * * *
WATCH_SERVICE_ACCOUNT=506739284793-compute@developer.gserviceaccount.com
WATCH_ATTEMPT_DEADLINE=180s
WATCH_MAX_RETRY_ATTEMPTS=3
WATCH_MIN_BACKOFF=5s
WATCH_MAX_BACKOFF=3600s
WATCH_MAX_DOUBLINGS=16

deploy:
	@case "$(SOLUTION)" in \
		rescue) \
			FUNCTION_NAME=email-to-telegram-rescue; \
			ENV_FILE=.env.rescue.yaml; \
			TRIGGER_TOPIC=gmail-notifications-rescue; \
			;; \
		retrieve) \
			FUNCTION_NAME=email-to-telegram-retrieve; \
			ENV_FILE=.env.retrieve.yaml; \
			TRIGGER_TOPIC=gmail-notifications-retrieve; \
			;; \
		*) \
			echo "Usage: make deploy SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions deploy $$FUNCTION_NAME \
		--entry-point=handle_request \
		--runtime=python310 \
		--trigger-topic=$$TRIGGER_TOPIC \
		--source=. \
		--env-vars-file=$$ENV_FILE \
		--region=$(REGION) \
		--project=$(PROJECT_ID)

deploy-rescue:
	$(MAKE) deploy SOLUTION=rescue

deploy-retrieve:
	$(MAKE) deploy SOLUTION=retrieve

deploy-all:
	$(MAKE) deploy-rescue
	$(MAKE) deploy-retrieve

deploy-watch:
	@case "$(SOLUTION)" in \
		rescue) \
			FUNCTION_NAME=renew-gmail-watch-rescue; \
			ENV_FILE=.env.rescue.yaml; \
			;; \
		retrieve) \
			FUNCTION_NAME=renew-gmail-watch-retrieve; \
			ENV_FILE=.env.retrieve.yaml; \
			;; \
		*) \
			echo "Usage: make deploy-watch SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions deploy $$FUNCTION_NAME \
		--entry-point=app \
		--runtime=python310 \
		--trigger-http \
		--no-allow-unauthenticated \
		--source=renew_watch \
		--env-vars-file=$$ENV_FILE \
		--region=$(REGION) \
		--project=$(PROJECT_ID)

deploy-watch-rescue:
	$(MAKE) deploy-watch SOLUTION=rescue

deploy-watch-retrieve:
	$(MAKE) deploy-watch SOLUTION=retrieve

deploy-watch-all:
	$(MAKE) deploy-watch-rescue
	$(MAKE) deploy-watch-retrieve

schedule-watch:
	@case "$(SOLUTION)" in \
		rescue) \
			JOB_NAME=renew-gmail-watch-rescue-job; \
			FUNCTION_NAME=renew-gmail-watch-rescue; \
			;; \
		retrieve) \
			JOB_NAME=renew-gmail-watch-retrieve-job; \
			FUNCTION_NAME=renew-gmail-watch-retrieve; \
			;; \
		*) \
			echo "Usage: make schedule-watch SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	URI=https://$(REGION)-$(PROJECT_ID).cloudfunctions.net/$$FUNCTION_NAME; \
	if gcloud scheduler jobs describe $$JOB_NAME \
		--location=$(REGION) \
		--project=$(PROJECT_ID) \
		>/dev/null 2>&1; then \
		echo "Updating Scheduler job $$JOB_NAME..."; \
		gcloud scheduler jobs update http $$JOB_NAME \
			--location=$(REGION) \
			--project=$(PROJECT_ID) \
			--schedule="$(WATCH_SCHEDULE)" \
			--time-zone="$(WATCH_TIME_ZONE)" \
			--uri="$$URI" \
			--http-method=GET \
			--oidc-service-account-email="$(WATCH_SERVICE_ACCOUNT)" \
			--oidc-token-audience="$$URI" \
			--attempt-deadline="$(WATCH_ATTEMPT_DEADLINE)" \
			--max-retry-attempts=$(WATCH_MAX_RETRY_ATTEMPTS) \
			--min-backoff="$(WATCH_MIN_BACKOFF)" \
			--max-backoff="$(WATCH_MAX_BACKOFF)" \
			--max-doublings=$(WATCH_MAX_DOUBLINGS); \
	else \
		echo "Creating Scheduler job $$JOB_NAME..."; \
		gcloud scheduler jobs create http $$JOB_NAME \
			--location=$(REGION) \
			--project=$(PROJECT_ID) \
			--schedule="$(WATCH_SCHEDULE)" \
			--time-zone="$(WATCH_TIME_ZONE)" \
			--uri="$$URI" \
			--http-method=GET \
			--oidc-service-account-email="$(WATCH_SERVICE_ACCOUNT)" \
			--oidc-token-audience="$$URI" \
			--attempt-deadline="$(WATCH_ATTEMPT_DEADLINE)" \
			--max-retry-attempts=$(WATCH_MAX_RETRY_ATTEMPTS) \
			--min-backoff="$(WATCH_MIN_BACKOFF)" \
			--max-backoff="$(WATCH_MAX_BACKOFF)" \
			--max-doublings=$(WATCH_MAX_DOUBLINGS); \
	fi

schedule-watch-rescue:
	$(MAKE) schedule-watch SOLUTION=rescue

schedule-watch-retrieve:
	$(MAKE) schedule-watch SOLUTION=retrieve

schedule-watch-all:
	$(MAKE) schedule-watch-rescue
	$(MAKE) schedule-watch-retrieve

delete-schedule-watch:
	@case "$(SOLUTION)" in \
		rescue) JOB_NAME=renew-gmail-watch-rescue-job ;; \
		retrieve) JOB_NAME=renew-gmail-watch-retrieve-job ;; \
		*) \
			echo "Usage: make delete-schedule-watch SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud scheduler jobs delete $$JOB_NAME \
		--location=$(REGION) \
		--project=$(PROJECT_ID)

delete-schedule-watch-rescue:
	$(MAKE) delete-schedule-watch SOLUTION=rescue

delete-schedule-watch-retrieve:
	$(MAKE) delete-schedule-watch SOLUTION=retrieve

logs:
	@case "$(SOLUTION)" in \
		rescue) FUNCTION_NAME=email-to-telegram-rescue ;; \
		retrieve) FUNCTION_NAME=email-to-telegram-retrieve ;; \
		*) \
			echo "Usage: make logs SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions logs read $$FUNCTION_NAME \
		--region=$(REGION) \
		--project=$(PROJECT_ID)

logs-watch:
	@case "$(SOLUTION)" in \
		rescue) FUNCTION_NAME=renew-gmail-watch-rescue ;; \
		retrieve) FUNCTION_NAME=renew-gmail-watch-retrieve ;; \
		*) \
			echo "Usage: make logs-watch SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions logs read $$FUNCTION_NAME \
		--region=$(REGION) \
		--project=$(PROJECT_ID)
