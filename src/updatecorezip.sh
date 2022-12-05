#!/bin/bash
echo "Delete old core.zip flie"
rm ./core.zip

echo "Create new core.zip file"
zip -r ./core.zip ./core