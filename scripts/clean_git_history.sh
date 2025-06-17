#!/bin/bash
# Script to remove sensitive files from git history
# WARNING: This rewrites git history!

echo "This script will remove sensitive files from git history."
echo "WARNING: This will rewrite git history. Make sure you have a backup!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Files to remove from history
FILES_TO_REMOVE=(
    "portfolio.db"
    "cookies.txt"
    "server.log"
    "logs/"
    "node_modules/"
    "staticfiles/"
)

echo "Removing files from git history..."
for file in "${FILES_TO_REMOVE[@]}"; do
    echo "Removing $file..."
    git filter-branch --force --index-filter \
        "git rm -r --cached --ignore-unmatch $file" \
        --prune-empty --tag-name-filter cat -- --all 2>/dev/null || true
done

echo "Cleaning up..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "Done! Files removed from history."
echo "You may need to force push if you've already pushed to a remote."