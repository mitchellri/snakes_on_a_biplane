#!/bin/bash


echo "=== ADD ALL FILES  ==="
git add -A;
echo "=== COMMIT CHANGES ==="
git commit -m "Next Iteration: `date +'%Y-%m-%d %H:%M:%S'`";
echo "===  PUSH TO GIT   ==="
git push origin master
echo "=== PUSH TO HEROKU ==="
git push heroku master