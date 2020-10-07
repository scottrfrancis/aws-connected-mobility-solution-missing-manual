#!/bin/bash

# CF - https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

cd transform/package
zip -r9 ../function.zip .

cd ..
zip -g function.zip lambda_function.py

aws lambda update-function-code --function-name nxp-sim-to-CMS --zip-file fileb://function.zip