PROJECT_ID=email-to-telegram-455900
REGION=us-central1

deploy:
	@case "$(SOLUTION)" in \
		rescue) \
			FUNCTION_NAME=renew-gmail-watch-rescue; \
			ENV_FILE=../.env.rescue.yaml; \
			;; \
		retrieve) \
			FUNCTION_NAME=renew-gmail-watch-retrieve; \
			ENV_FILE=../.env.retrieve.yaml; \
			;; \
		*) \
			echo "Usage: make deploy SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions deploy $$FUNCTION_NAME \
		--entry-point=app \
		--runtime=python310 \
		--trigger-http \
		--allow-unauthenticated \
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

logs:
	@case "$(SOLUTION)" in \
		rescue) FUNCTION_NAME=renew-gmail-watch-rescue ;; \
		retrieve) FUNCTION_NAME=renew-gmail-watch-retrieve ;; \
		*) \
			echo "Usage: make logs SOLUTION=rescue|retrieve"; \
			exit 1; \
			;; \
	esac; \
	gcloud functions logs read $$FUNCTION_NAME \
		--region=$(REGION) \
		--project=$(PROJECT_ID)
