PROJECT_ID=email-to-telegram-455900
REGION=us-central1
FUNCTION_NAME=email-to-telegram
TRIGGER_TOPIC=gmail-notifications
ENV_FILE=.env.rescue.yaml

deploy:
	gcloud functions deploy $(FUNCTION_NAME) \
		--entry-point=handle_request \
		--runtime=python310 \
		--trigger-topic=$(TRIGGER_TOPIC) \
		--source=. \
		--env-vars-file=$(ENV_FILE) \
		--region=$(REGION) \
		--project=$(PROJECT_ID)

logs:
	gcloud functions logs read $(FUNCTION_NAME) --region=$(REGION) --project=$(PROJECT_ID)
