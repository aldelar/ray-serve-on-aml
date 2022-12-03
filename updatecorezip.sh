#!/bin/bash
echo "Delete old core.zip flie"
rm ./src/core.zip

echo "Create new core.zip file"
zip -r ./src/core.zip ./src/core