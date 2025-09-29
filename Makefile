dev:
	@echo "Setting up development environment..."
	@# Check for Node.js dependencies
	@if [ -f "package.json" ]; then \
		echo "Installing Node.js dependencies..."; \
		npm install; \
		# Consider running npm audit fix for security fixes:
		# npm audit fix || true; \
		fpm start || true; \
	fi

	@# Check for Python dependencies
	@if [ -f "requirements.txt" ]; then \
		echo "Installing Python dependencies..."; \
		pip install -r requirements.txt; \
	fi

	@echo ""
	@echo "Dev environment ready! Run your app with npm start or python app.py"
