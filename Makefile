
test-all:
	echo "\n\n\033[32mRunning tests and other goodies...\033[0m" \
	ruff check . --output-format=concise ; \
	ty check . ; \
	typos . && printf "\033[32mSyntax good 😌\033[0m\n" || true
