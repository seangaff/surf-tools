DOWNLOAD_SCRIPT = downloadStills.py
SESSION_NAME = download_stills
DOWNLOAD_LOG = download.log


.PHONY: download_stills
download_stills:
	@echo "Starting download loop" 
	@screen -dmS $(SESSION_NAME) bash -c "cd utilities && python $(DOWNLOAD_SCRIPT) 2>&1 | tee $(DOWNLOAD_LOG)"
	@echo "Script started in background. Use 'make status' to check if running."

.PHONY: status
status:
	@echo "Checking status of '$(SESSION_NAME)'..."
	@screen -ls | grep $(SESSION_NAME) && echo "✓ Running" || echo "✗ Not running"
	@ps aux | grep -v grep | grep "$(DOWNLOAD_SCRIPT)" || true

.PHONY: stop
stop:
	@if ! screen -ls | grep -q $(SESSION_NAME); then \
		echo "Session '$(SESSION_NAME)' not found."; \
		exit 1; \
	fi
	@echo "Stopping screen session '$(SESSION_NAME)'..."
	@screen -S $(SESSION_NAME) -X quit
	@echo "Stopped."